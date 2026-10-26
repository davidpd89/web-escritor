import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CLSTraceBoundaryRuntime(unittest.TestCase):
    def test_exact_one_second_gap_starts_new_window(self):
        script = r'''const fs=require('fs');
const vm=require('vm');
const source=fs.readFileSync('qa/cls-trace.mjs','utf8');
const start=source.indexOf('      await page.addInitScript(() => {');
const end=source.indexOf('\n      let result;',start);
if(start<0||end<0)throw Error('CLS observer block not found');
const block=source.slice(start,end);
const fn=block.match(/await page\.addInitScript\((\(\) => \{[\s\S]*\})\);\s*$/);
if(!fn)throw Error('CLS initialization callback not found');
let observer;
const document={fonts:null};
const window={};
class PerformanceObserver{constructor(cb){observer=cb;}observe(){}}
vm.runInNewContext('('+fn[1]+')()', {window,document,PerformanceObserver});
const entry=(time,value)=>({startTime:time,value,hadRecentInput:false,sources:[]});
observer({getEntries:()=>[entry(100,0.12),entry(1100,0.08),entry(1200,0.04)]});
process.stdout.write(JSON.stringify(window.__clsTrace));'''
        result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f'qa/cls-trace.mjs: {result.stderr}')
        data = json.loads(result.stdout)
        self.assertEqual(len(data['shifts']), 3, 'qa/cls-trace.mjs: faltan desplazamientos')
        self.assertAlmostEqual(data['total'], 0.12, places=5, msg=f'qa/cls-trace.mjs: CLS máximo incorrecto: {data["total"]}')

if __name__ == '__main__':
    unittest.main()