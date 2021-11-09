select 
  g."id_i",
  g."parent_id_i",
  g."path_i",
  s.$sFrom$ as "from_h", 
  g."type_i",
  g."groupType",
  g."groupCount"
from (
  select
      cast(max(cast(scs."locid_i" as varchar)) as uuid) as "id_i",
      scs."sid_i" as "parent_id_i",
      $path('/sources/locationStats')$ as "path_i",
      $type()$ as "type_i",
      scs."groupType",
      count(*) as "groupCount" 
  from ((select 
        s.$sId$ as "sid_i",
        loc.$locId$ as "locid_i",
        md."name" as "groupType" 
        from $s$ s
          join "location_a" loca on s.id_i = loca.ancestor_id 
            join $loc$ loc on loc.$locId$ = loca.base_id 
              join "_MmdDictionary" md on md.id = loc.$locType$)
              union all 
        (select 
        s.$sId$ as "sid_i",
        fol.$folId$ as "folid_i",
        md."name" as "groupType" 
        from $s$ s
          join "folder_a" foldera on s.id_i = foldera.ancestor_id 
            join $fol$ fol on fol.$folId$ = foldera.base_id 
              join "_MmdDictionary" md on md.id = fol.$folType$)) scs
  group by scs."sid_i", scs."groupType"
) g
  join $s$ s on s.$sId$ = g."parent_id_i"
