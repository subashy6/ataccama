/*
 * This query computes the relevant anomalyExplanations for an attribute entity.
 * The relevant is chosen as: 
 * The anomalyExplanations of the latest anomaly state from a FULL profile
 *
 * This is a workaround, because Computed Content doesn't support nested
 * computed contents. The query is almost identical to attributeAnomalyState.sql.
 *
 *
 * The MMD database structure of the profiling portion of the app:
 *
 *   --------------- 1    * ---------------------------------- 
 *  | catalogItem_p |-----<| profilingConfigurationInstance_p |
 *   ---------------        ---------------------------------- 
 *                                            1 |
 *                                              |
 *                                            * ∧
 *                            0..1 --------------------------- 
 *              ------------------|   catalogItemProfile_p    |
 *             |            1     |---------------------------|
 *             |                  | *profiledAt_s:  timestamp |
 *             |                  | *profileType_s: varchar   |
 *             |                   --------------------------- 
 *             |                              1 |
 *           1 |                                |
 *   ----------------------                   * ∧
 *  |    anomalyState_p    |   0..1 -------------------------- 
 *  |----------------------|-------|    attributeProfile_p    |
 *  | *state_s:    varchar |1       -------------------------- 
 *  | *feedback_s: varchar |                  * | SRE:
 *   ----------------------                     | attribute_ri
 *           1 |                              1 |
 *             |                    -------------------------- 
 *           * ∧                   |        attribute_p       |
 *   --------------------------     --------------------------                        
 *  |   anomalyExplanation_p   |                              
 *  |--------------------------|                              
 *  | *state_s:       varchar  |                              
 *  | *explanation_s: varchar  |                              
 *  | *category_s:    varchar  |                              
 *   --------------------------                               
 *
 * ------------------------------ Aliases -------------------------------
 * 
 * attribute: attribute
 *   - ID:          aId
 *   - FROM:        aFrom
 *   - PATH:        aPath
 *
 * catalogItemProfile: catalogItemProfile
 *   - ID:          cpId
 *   - profiledAt:  cpProfiledAt
 *   - profileType: cpProfiledType
 *
 * anomalyState: anomalyState
 *   - ID:          sId
 *   - PARENT_ID:   sParentId
 *   - state:       sState
 *   - feedback:    sFeedback
 * 
 * anomalyExplanation: anomalyExplanation
 *   - ID:          eId
 *   - PARENT_ID:   eParentId
 *   - state:       eState
 *   - explanation: eExplanation
 *   - category:    eCategory
 *
 * attributeProfile: attributeProfile
 *   - ID:          pId
 *   - PARENT_ID:   pParentId
 *
 * ------------------------ Computed properties -------------------------
 * 
 * explanation:            String
 * state:                  String
 * category:               String
 */


select
    anomalyExplanation.$eId$ as "id_i",
    attribute.$aId$ as "parent_id_i",
    attribute.$aFrom$ as "from_h",
    $path(attribute.$aPath$)$ as "path_i",
    $type()$ as "type_i",
    anomalyExplanation.$eState$ as "state",
    anomalyExplanation.$eExplanation$ as "explanation",
    anomalyExplanation.$eCategory$ as "category"
from $anomalyState$ anomalyState
    join $attributeProfile$ attributeProfile on anomalyState.$sParentId$=attributeProfile.$pId$
    -- Here we find the relevant attribute
    join $attribute$ attribute on attributeProfile."attribute_ri"=attribute.$aId$
    -- We need to find the relevant catalogItemProfile to select the latest and filter by FULL profiles
    join $catalogItemProfile$ catalogItemProfile on attributeProfile.$pParentId$=catalogItemProfile.$cpId$
    -- Finally We find all the relevant explanations
    join $anomalyExplanation$ anomalyExplanation on anomalyExplanation.$eParentId$=anomalyState.$sId$
where
    -- We consider only FULL profiles
    catalogItemProfile.$cpProfileType$ = 'FULL'
    -- Here we need to find the latest. The date is indicated by the 'profiledAt' property
    -- (select the one which equals to the maximal value of profiledAt)
    and (catalogItemProfile.$cpProfiledAt$ = 
    (select max(cpInner.$cpProfiledAt$)
        from $attributeProfile$ apInner 
        -- Filter only profiles belonging to the given attribute: join attributeProfile -> attribute
        join $attribute$ aInner on apInner."attribute_ri"=attribute.$aId$
        -- Find the parent catalogItemProfiles
        join $catalogItemProfile$ cpInner on apInner.$pParentId$=cpInner.$cpId$
    -- Filter by FULL profiles
    where cpInner.$cpProfileType$ = 'FULL'
    ))
