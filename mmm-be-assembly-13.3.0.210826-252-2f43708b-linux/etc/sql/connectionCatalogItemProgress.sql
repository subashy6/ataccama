SELECT
    con.$conId$ as "id_i",
    con.$conId$ as "parent_id_i",
    con.$conFrom$ as "from_h",
    $path('/sources/connections/catalogItemStates')$ as "path_i",
    $type()$ as "type_i",
    count(*) as "totalCount",
    count(fullResult.fullResultId) as "profiledCount",
    count(sampleResult.sampleResultId) as "sampledCount",
    count(dq."id_i") as "dqCount"
FROM $con$ con 
join $ci$ ci on con.$conId$ = ci.connection_ri
LEFT JOIN (
    SELECT
        fullPci.$pciParentId$ as fullResultParentId, fullPci.$pciId$ as fullResultId
    FROM $pci$ fullPci 
    INNER JOIN $procon$ fullProcon
    ON fullProcon.$proconId$ = fullPci."configuration_ri" and fullProcon.$proconType$ = 'FULL'
) AS fullResult ON ci.$ciId$ = fullResult.fullResultParentId
LEFT JOIN (
    SELECT
        samplePci.$pciParentId$ as sampleResultParentId, samplePci.$pciId$ as sampleResultId
    FROM $pci$ samplePci 
    INNER JOIN $procon$ sampleProcon
    ON sampleProcon.$proconId$ = samplePci."configuration_ri" and sampleProcon.$proconType$ = 'SAMPLE'
) AS sampleResult ON ci.$ciId$ = sampleResult.sampleResultParentId
LEFT JOIN $dqEval$ dq on dq.$dqEvalParentId$ = ci.$ciId$
GROUP BY con.$conId$, con.$conFrom$
