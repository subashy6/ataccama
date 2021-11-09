/*
 * This query computes the relevant anomalyState for a catalogItem entity.
 * The relevant is chosen as: The latest anomaly state from a FULL profile
 *
 * The MMD database structure of the profiling portion of the app:
 *
 *   --------------- 1    * ---------------------------------- 
 *  | catalogitem_p |-----<| profilingconfigurationinstance_p |
 *   ---------------        ---------------------------------- 
 *                                            1 |
 *                                              |
 *                                            * ∧
 *   ----------------------   0..1 --------------------------- 
 *  |    anomalystate_p    |------|   catalogitemprofile_p    |
 *  |----------------------|1     |---------------------------|
 *  | *state_s:    varchar |      | *profiledat_s:  timestamp |
 *  | *feedback_s: varchar |      | *profiletype_s: varchar   |
 *   ----------------------        --------------------------- 
 *             |1                             1 |
 *             |                                |
 *             |                              * ∧
 *             |               0..1 -------------------------- 
 *              -------------------|    attributeprofile_p    |
 *                                  -------------------------- 
 *                                 
 *
 * We want to compute two different information from the latest profiles: 
 *   1. anomalyState on the catalogItem level
 *   2. number of anomalous attributes 
 *      (anomalyStates on the attribute level)
 *
 * ------------------------------ Aliases -------------------------------
 * 
 * catalogItem: catalogItem
 *   - ID:          ciId
 *   - FROM:        ciFrom
 *   - PATH:        ciPath
 *
 * profilingConfigurationInstance: profilingConfigurationInstance
 *   - ID:          pcId
 *   = PARENT_ID:   pcParentId
 * 
 * catalogItemProfile: catalogItemProfile
 *   - ID:          cpId
 *   = PARENT_ID:   cpParentId
 *   - profiledAt:  cpProfiledAt
 *   - profileType: cpProfiledType
 *
 * anomalyState: anomalyState
 *   - ID:          sId
 *   - PARENT_ID:   sParentId
 *   - state:       sState
 *   - feedback:    sFeedback
 *
 * attributeProfile: attributeProfile
 *   - ID:          apId
 *   - PARENT_ID:   apParentId
 *
 * ------------------------ Computed properties -------------------------
 * 
 * state:                  String
 * feedback:               String
 * catalogItemProfileGid:  String
 * numAnomalousAttributes: Integer
 * 
 */

select
    -- The ID is the same as the in original anomalyState entity, which is intended and used on frontend
    anomalyState.$sId$ as "id_i",
    catalogItem.$ciId$ as "parent_id_i",
    catalogItem.$ciFrom$ as "from_h",
    $path(catalogItem.$ciPath$)$ as "path_i",
    $type()$ as "type_i",
    anomalyState.$sState$ as "state",
    anomalyState.$sFeedback$ as "feedback",
    -- This ID is required by frontend to be able to open anomaly inspector on any page
    catalogItemProfile.$cpId$ as "catalogItemProfileGid",
    catalogItemProfile.$cpProfiledAt$ as "profiledAt",

    -- Here we compute the number of anomalous attributes 
    -- by counting all attributeProfiles which have anomalyState with state='TRUE'
    (select count(sInner.$sId$)
        from 
            -- Select all attribute profiles belonging to the catalogItemProfile we found earlier
            (select apInner.$apId$ from $attributeProfile$ apInner where apInner.$apParentId$=catalogItemProfile.$cpId$) as apInner 
            -- Find their anomaly states
            join $anomalyState$ sInner on sInner.$sParentId$=apInner.$apId$
        where
            -- We count only those attributes which have anomalyState with state='TRUE' and the user didn't explicitly say it's 'NOT_ANOMALY'
            sInner.$sState$='TRUE' and sInner.$sFeedback$!='NOT_ANOMALY'
    ) as "numAnomalousAttributes"
from
    $anomalyState$ anomalyState
    join $catalogItemProfile$ catalogItemProfile on anomalyState.$sParentId$=catalogItemProfile.$cpId$
    -- We need to filter only those profiles belonging to the given catalogItem, hence we need to join
    -- all the way through catalogItemProfile -> profilingConfigurationInstance -> catalogItem
    join $profilingConfigurationInstance$ profilingConfigurationInstance on profilingConfigurationInstance.$pcId$=catalogItemProfile.$cpParentId$
    join $catalogItem$ catalogItem on profilingConfigurationInstance.$pcParentId$=catalogItem.$ciId$
where
    -- We consider only FULL profiles
    catalogItemProfile.$cpProfileType$ = 'FULL'
    -- Here we need to find the latest. The date is indicated by the 'profiledAt' property
    -- (select the one which equals to the maximal value of profiledAt)
    and (catalogItemProfile.$cpProfiledAt$ = 
    (select max(cpInner.$cpProfiledAt$)
    from $catalogItemProfile$ cpInner
    -- Again, we need to filter only those profiles belonging to the given catalogItem, hence we need to join
    -- all the way through catalogItemProfile -> profilingConfigurationInstance -> catalogItem
    join $profilingConfigurationInstance$ pcInner on cpInner.$cpParentId$=pcInner.$pcId$
    join $catalogItem$ ciInner on pcInner.$pcParentId$=catalogItem.$ciId$
    where cpInner.$cpProfileType$ = 'FULL'))
