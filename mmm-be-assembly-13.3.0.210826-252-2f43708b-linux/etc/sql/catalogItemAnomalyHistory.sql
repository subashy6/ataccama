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
 *   - profileType: cpProfileType
 *
 * anomalyState: anomalyState
 *   - ID:          sId
 *   - PARENT_ID:   sParentId
 *   - FROM:        sFrom
 *   - state:       sState
 *   - feedback:    sFeedback
 *
 * attributeProfile: attributeProfile
 *   - ID:          apId
 *
 * ------------------------ Computed properties -------------------------
 * 
 * state:                  String
 * feedback:               String
 * catalogItemProfileGid:  String
 * catalogItemId:          String
 * numAnomalousAttributes: Integer
 * 
 */

select
    -- The ID is the same as the in original anomalyState entity, which is intended and can used on frontend
    anomalyState.$sId$ as "id_i",
    catalogItem.$ciId$ as "parent_id_i",
    catalogItem.$ciId$ as "catalogItemGid",
    anomalyState.$sFrom$ as "from_h",
    $path(catalogItem.$ciPath$)$ as "path_i",
    $type()$ as "type_i",
    anomalyState.$sState$ as "state",
    anomalyState.$sFeedback$ as "feedback",
    -- This ID is required by frontend to be able to open anomaly inspector on any page
    catalogItemProfile.$cpId$ as "catalogItemProfileGid",
    catalogItemProfile.$cpProfiledAt$ as "profiledAt",
    t1."numAnomalousAttributes"

from
    $anomalyState$ anomalyState
    join $catalogItemProfile$ catalogItemProfile on anomalyState.$sParentId$=catalogItemProfile.$cpId$
    -- We need to filter only those profiles belonging to the given catalogItem, hence we need to join
    -- all the way through catalogItemProfile -> profilingConfigurationInstance -> catalogItem
    join $profilingConfigurationInstance$ profilingConfigurationInstance on profilingConfigurationInstance.$pcId$=catalogItemProfile.$cpParentId$
    join $catalogItem$ catalogItem on profilingConfigurationInstance.$pcParentId$=catalogItem.$ciId$

  	-- This nested select will give us the number of anomalous attribute profiles for each catalogItemProfile
	join (
		select
			cpInner.$cpId$ as cpInnerId,
			count(sInner.$sId$) as "numAnomalousAttributes"
		from 
			-- Start from all catalogItemProfiles
			$catalogItemProfile$ cpInner
			-- Find attributeProfiles that belong to them
			join $attributeProfile$ apInner on apInner.parent_id_i = cpInner.$cpId$
			-- Find their anomalyStates
			join $anomalyState$ sInner on sInner.parent_id_i=apInner.$apId$
		where
            -- We only consider FULL profiles
            cpInner.$cpProfileType$='FULL' 
            and
			-- We count only those attributes which have anomalyState with state='TRUE' and the user didn't explicitly say it's 'NOT_ANOMALY'
            sInner.$sState$='TRUE' and sInner.$sFeedback$!='NOT_ANOMALY'
		group by cpInner.$cpId$
	) t1 on t1.cpInnerId=catalogItemProfile.$cpId$

where
    -- We only consider FULL profiles
    catalogItemProfile.$cpProfileType$='FULL' 
    and 
	-- We count only those catalogItem profiles which have at least one anomalous attribute OR
	-- it's own anomalyState with state='TRUE' and the user didn't explicitly say it's 'NOT_ANOMALY'
    (t1."numAnomalousAttributes" > 0 or (anomalyState.$sState$='TRUE' and anomalyState.$sFeedback$!='NOT_ANOMALY'))
order by
	catalogItemProfile.$cpProfiledAt$ desc
