select
    a.$aId$ as "id_i",
    a.$aId$ as "parent_id_i",
    a.$aFrom$ as "from_h",
    ci.$ciName$ as "name",
    ci.$ciOriginPath$ as "originPath",
    mtci.$mtciPartitions$ as "partitions",
    $path(a.$aPath$)$ as "path_i",
    $type()$ as "type_i"
from $a$ a
    join $ci$ ci on ci.$ciId$ = a.$aParentId$
    join $mtci$ mtci on mtci.$mtciId$ = a.$aParentId$
