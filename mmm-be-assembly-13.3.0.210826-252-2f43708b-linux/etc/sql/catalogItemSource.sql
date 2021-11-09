SELECT 
    ci.$ciId$ as "id_i",
    ci.$ciId$ as "parent_id_i",
    $path(ci.$ciPath$)$ as "path_i",
    $type()$ as "type_i",
    ci.$ciFrom$ as "from_h",
    cia.ancestor_id as "sourceId"
FROM $ci$ ci join "catalogItem_a" cia on ci.$ciId$ = cia.base_id
WHERE cia.ancestor_type = $type('source')$
    
