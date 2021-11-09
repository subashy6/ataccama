select
    t.$tId$ as "id_i",
    "assignedTerms"."catalogItem_id" as "parent_id_i",
    t.$tFrom$ as "from_h",
    $path("assignedTerms".$ciPath$)$ as "path_i",
    $type()$ as "type_i",
    t.$tName$ as "term_name",
    t.$tPath$ as "term_path",
    md."name" as "term_type",
    "assignedTerms"."term_depth"
from (select
          ti.target_ri as "term_id",
          ci.$tId$ as "catalogItem_id",
          ci.$ciPath$,
          min(tia.ancestor_distance) as "term_depth"
      from $ci$ ci
               join "termInstance_a" tia on tia.ancestor_id = ci.$ciId$
               join $ti$ ti on ti.$tiId$ = tia.base_id
               join "_MmdDictionary" mdPath on mdPath.id = ti.$tiPath$
      where mdPath."name" not like '%/hiddenTermInstances'
      group by ti.target_ri, ci.$tId$, ci.$ciPath$) "assignedTerms"
         join $t$ t on t.$tId$ = "assignedTerms"."term_id"
         join "_MmdDictionary" md on md.id = t.$tType$
