select distinct on (ci.$ciId$)
    ci.$ciId$ as "id_i",
    ci.$ciId$ as "parent_id_i",
    ci.$ciFrom$ as "from_h",
    p.$pNumberOfRecords$ as "numberOfRecords",
    $path(ci.$ciPath$)$ as "path_i",
    $type()$ as "type_i"
from $pci$ pci
    join $p$ p on pci.$pciId$ = p.$pParentId$
    join $ci$ ci on pci.$pciParentId$ = ci.$ciId$
order by ci.$ciId$, p.$pFrom$ desc
