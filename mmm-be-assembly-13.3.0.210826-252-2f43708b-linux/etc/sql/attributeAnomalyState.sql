/*
 * This query computes the relevant anomalyState for an attribute entity.
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
 *             | 1                            1 |
 *             |                                |
 *             |                              * ∧
 *             |               0..1 --------------------------
 *             --------------------|    attributeprofile_p    |
 *                                  --------------------------
 *                                            * | SRE:
 *                                              | attribute_ri
 *                                            1 |
 *                                  --------------------------
 *                                 |        attribute_p       |
 *                                  --------------------------
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
 * attributeProfile: attributeProfile
 *   - ID:          pId
 *   - PARENT_ID:   pParentId
 *
 * ------------------------ Computed properties -------------------------
 * 
 * state:                  String
 * feedback:               String
 * catalogItemProfileGid:  String
 * profiledAt:             Timestamp
 */

select
    anomalyState.$sId$ as "id_i",
    attribute.$aId$ as "parent_id_i",
    attribute.$aFrom$ as "from_h",
    catalogItemProfile.$cpId$ as "catalogItemProfileGid",
    catalogItemProfile.$cpProfiledAt$ as "profiledAt",
    $path(attribute.$aPath$)$ as "path_i",
    $type()$ as "type_i",
    anomalyState.$sState$ as "state",
    anomalyState.$sFeedback$ as "feedback"
from $anomalyState$ anomalyState
    join $attributeProfile$ attributeProfile on anomalyState.$sParentId$=attributeProfile.$pId$
    -- Here we find the relevant attribute
    join $attribute$ attribute on attributeProfile."attribute_ri"=attribute.$aId$
    -- We need to find the relevant catalogItemProfile to select the latest and filter by FULL profiles
    join $catalogItemProfile$ catalogItemProfile on attributeProfile.$pParentId$=catalogItemProfile.$cpId$
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
