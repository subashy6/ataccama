select
    t.$tId$ as "id_i",
    t.$tId$ as "parent_id_i",
    t.$tFrom$ as "from_h",
    $path(t.$tPath$)$ as "path_i",
    $type()$ as "type_i",
    case when "c"."c" is null then 0 else "c"."c" end as "c"
from $t$ t    
    left join (
        select
            count(*) as "c",
            ci.$cParentId$ as parent_id_i
        from $c$ ci
        group by ci.$cParentId$) "c"
        on t.$tId$ = "c".parent_id_i
