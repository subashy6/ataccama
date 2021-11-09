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
      cast(max(cast(scs."cid_i" as varchar)) as uuid) as "id_i",
      scs."sid_i" as "parent_id_i",
      $path('/sources/catalogItemStats')$ as "path_i",
      $type()$ as "type_i",
      scs."groupType",
      count(*) as "groupCount" 
  from (select 
           s.$sId$ as "sid_i",
           ci.$ciId$ as "cid_i",
           case coalesce(ci."tableType_s", md."name")
           when 'fileCatalogItem' then 'FILE'
           else coalesce(ci."tableType_s", md."name")
           end as "groupType"
        from $s$ s
          join "catalogItem_a" cia on s.id_i = cia.ancestor_id 
            join $ci$ ci on ci.$ciId$ = cia.base_id 
              join "_MmdDictionary" md on md.id = ci.$ciType$ ) scs
  group by scs."sid_i", scs."groupType"
) g
  join $s$ s on s.$sId$ = g."parent_id_i"
