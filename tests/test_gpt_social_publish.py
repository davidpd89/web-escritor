from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import gpt_social_publish as pub  # noqa: E402
import gpt_social_compose as compose  # noqa: E402

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
IDS = list(compose.PROFILES)


def snapshot(followers=100, generated=NOW, valid_hours=47):
    stamp = generated.strftime("%Y-%m-%dT%H:%M:%SZ")
    until = (generated + timedelta(hours=valid_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return json.dumps({"schema_version": 1, "generated_at": stamp, "networks": [
        {"id": i, "profile_url": compose.PROFILES[i], "followers": followers, "observed_at": stamp,
         "valid_until": until, "status": "ok"} for i in IDS],
        "totals": {"follower_relationships": followers * len(IDS), "valid_until": until}}, indent=2) + "\n"


def run(cwd, *a):
    r = subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bare = self.tmp / "remote.git"
        run(self.tmp, "init", "--bare", "-b", "main", str(self.bare))
        self.seed = self.tmp / "seed"
        run(self.tmp, "clone", "-q", str(self.bare), str(self.seed))
        run(self.seed, "config", "user.name", "t")
        run(self.seed, "config", "user.email", "t@t")
        (self.seed / "redes-sociales").mkdir()
        (self.seed / "redes-sociales/social-metrics.json").write_text(snapshot(100, NOW - timedelta(days=1)))
        (self.seed / "other.txt").write_text("x")
        run(self.seed, "add", "-A")
        run(self.seed, "commit", "-qm", "seed")
        run(self.seed, "push", "-q", "origin", "HEAD:main")
        self.src = self.tmp / "src.json"
        self.clone = self.tmp / "clone"

    def go(self, text, **kw):
        self.src.write_text(text)
        return pub.publish(self.src, self.clone, str(self.bare), now=NOW, **kw)

    def remote_files(self, ref="main"):
        return run(self.bare, "diff", "--name-only", f"{ref}~1", ref).split()

    def test_data_only_publication(self):
        self.assertEqual(self.go(snapshot(150)), "published")
        self.assertEqual(self.remote_files(), ["redes-sociales/social-metrics.json"])
        self.assertEqual(run(self.bare, "rev-list", "--count", "main"), "2")

    def test_identical_data_is_noop(self):
        self.go(snapshot(150))
        head = run(self.bare, "rev-parse", "main")
        self.assertEqual(self.go(snapshot(150)), "noop")
        self.assertEqual(run(self.bare, "rev-parse", "main"), head)

    def test_not_due_when_recent_and_not_expiring(self):
        self.go(snapshot(150))
        head = run(self.bare, "rev-parse", "main")
        later = NOW + timedelta(hours=2)
        self.src.write_text(snapshot(160, later))
        self.assertEqual(pub.publish(self.src, self.clone, str(self.bare), now=later), "not-due")
        self.assertEqual(run(self.bare, "rev-parse", "main"), head)

    def test_republishes_near_expiry_even_if_values_same(self):
        self.go(snapshot(150))
        later = NOW + timedelta(hours=36)
        self.src.write_text(snapshot(150, later))
        self.assertEqual(pub.publish(self.src, self.clone, str(self.bare), now=later), "published")

    def test_remote_main_moves_before_push_is_rebased_not_overwritten(self):
        def move_remote():
            (self.seed / "other.txt").write_text("unrelated work")
            run(self.seed, "commit", "-qam", "unrelated")
            run(self.seed, "push", "-q", "origin", "HEAD:main")
        self.assertEqual(self.go(snapshot(150), before_push=move_remote), "published")
        self.assertEqual(run(self.bare, "show", "main:other.txt"), "unrelated work")
        self.assertEqual(self.remote_files(), ["redes-sociales/social-metrics.json"])

    def test_invalid_or_private_data_rejected(self):
        head = run(self.bare, "rev-parse", "main")
        for bad in ("not json", snapshot(150).replace('"status": "ok"', '"status": "ok", "brandId": "1"', 1),
                    snapshot(150, NOW - timedelta(days=5))):
            with self.assertRaises(pub.PublishError):
                self.go(bad)
        self.assertEqual(run(self.bare, "rev-parse", "main"), head)

    def test_failed_push_leaves_remote_intact_and_clone_recovers(self):
        hook = self.bare / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        head = run(self.bare, "rev-parse", "main")
        with self.assertRaises(pub.PublishError):
            self.go(snapshot(150))
        self.assertEqual(run(self.bare, "rev-parse", "main"), head)
        hook.unlink()
        self.assertEqual(self.go(snapshot(150)), "published")  # clone self-heals on next run

    def test_feature_branch_commits_never_reach_main(self):
        # the caller's worktree is irrelevant: only the dedicated clone pushes, and only one data commit
        run(self.seed, "checkout", "-qb", "feature")
        (self.seed / "feature.txt").write_text("wip")
        run(self.seed, "add", "-A")
        run(self.seed, "commit", "-qm", "feature work")
        self.go(snapshot(150))
        self.assertNotIn("feature.txt", run(self.bare, "ls-tree", "--name-only", "main"))
        self.assertEqual(run(self.bare, "rev-list", "--count", "main"), "2")

    def test_hung_git_becomes_publish_error_without_prompting(self):
        seen = {}

        def hang(argv, **kw):
            seen.update(kw)
            raise subprocess.TimeoutExpired(argv, kw["timeout"])

        original = pub.subprocess.run
        pub.subprocess.run = hang
        try:
            with self.assertRaises(pub.PublishError):
                pub.git(self.tmp, "fetch", "origin")
        finally:
            pub.subprocess.run = original
        self.assertEqual(seen["env"]["GIT_TERMINAL_PROMPT"], "0")
        self.assertGreater(seen["timeout"], 0)


if __name__ == "__main__":
    unittest.main()
