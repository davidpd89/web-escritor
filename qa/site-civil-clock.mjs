const SITE_TIME_ZONE='Europe/Madrid';

export function siteCivilDate(value=new Date()){
  const instant=value instanceof Date?value:new Date(value);
  if(Number.isNaN(instant.getTime())) return null;
  const parts=Object.fromEntries(
    new Intl.DateTimeFormat('en-US',{
      timeZone:SITE_TIME_ZONE,
      year:'numeric',
      month:'2-digit',
      day:'2-digit',
    }).formatToParts(instant).filter(part=>part.type!=='literal').map(part=>[part.type,part.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

export { SITE_TIME_ZONE };
