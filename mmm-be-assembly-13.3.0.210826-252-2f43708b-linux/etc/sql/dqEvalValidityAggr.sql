select
    aggr.$aggrId$ as "id_i",
    aggr.$aggrId$ as "parent_id_i",
    aggr.$aggrFrom$ as "from_h",
    COALESCE(valid."resultCount_s", 0) as "validCount",
    COALESCE(valid."color_s", 'green') as "validColor",
    COALESCE(invalid."resultCount_s", 0) as "invalidCount",
    COALESCE(invalid."color_s", 'red') as "invalidColor",
    round(100.0 * COALESCE(valid."resultCount_s", 0) / NULLIF(COALESCE(invalid."resultCount_s", 0) + COALESCE(valid."resultCount_s", 0),0), 2) as "overallQuality",
    $path(aggr.$aggrPath$)$ as "path_i",
    $type()$ as "type_i"
from $aggr$ aggr
    left join $dqDim$ dqDim on dqDim."name_s" = 'Validity'
    left join $dimAggr$ dimAggr on dqDim.$dqDimId$ = dimAggr."dqDimension_ri" AND dimAggr.$dimAggrPid$ = aggr.$aggrId$ AND dimAggr."ruleCount_s" IS NULL
    left join (
        select dimAggrResult.$dimAggrResultPid$ as parent_id_i,
               dimAggrResult."resultCount_s" as "resultCount_s",
               dqDimResult.color_s as color_s
        from $dimAggrResult$ dimAggrResult
        left join $dqDimResult$ dqDimResult on dqDimResult.$dqDimResultId$ = dimAggrResult.result_ri
             where (dqDimResult.name_s = 'Valid')) valid on (valid.parent_id_i = dimAggr.$dimAggrId$)
    left join (
         select dimAggrResult.$dimAggrResultPid$ as parent_id_i,
                dimAggrResult."resultCount_s" as "resultCount_s",
                dqDimResult.color_s as color_s
         from $dimAggrResult$ dimAggrResult
         left join $dqDimResult$ dqDimResult on dqDimResult.$dqDimResultId$ = dimAggrResult.result_ri
              where (dqDimResult.name_s = 'Invalid')) invalid on (invalid.parent_id_i = dimAggr.$dimAggrId$)
