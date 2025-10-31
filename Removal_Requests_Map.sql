-- Filter data from 2019-2024 for analysis
CREATE TABLE ggrr_prod_reason AS
SELECT * FROM google_government_detailed_removal_requests
WHERE `Period Ending` >= '2019-06-30';

SELECT * FROM ggrr_prod_reason;

-- Convert date strings to proper DATE format
UPDATE google_government_removal_requests
SET `Period Ending` = str_to_date(`Period Ending`, '%d/%m/%Y'); 

ALTER TABLE google_government_removal_requests
MODIFY COLUMN `Period Ending` DATE;

-- Rename table for easier reference
RENAME TABLE google_government_removal_requests TO ggrr_item_perc;

-- Replace NULL percentage values with 0 for calculations
UPDATE ggrr_item_perc
SET 
	`% Removed-Legal` = ifnull(`% Removed-Legal`, 0),
	`% Removed-Policy` = ifnull(`% Removed-Policy`, 0),
	`% Content Already Removed` = ifnull(`% Content Already Removed`, 0),
	`% Content Not Found` = ifnull(`% Content Not Found`, 0),
	`% Not Enough Information` = ifnull(`% Not Enough Information`, 0),
	`% No Action Taken` = ifnull(`% No Action Taken`, 0);
	
-- Data quality check: find records where percentages don't sum to ~100%
SELECT *
FROM ggrr_item_perc gip 
WHERE (`% Removed-Legal`+ `% Removed-Policy`+ `% Content Not Found`+ `% Content Already Removed`+ `% Not Enough Information`+ `% No Action Taken`) <> 100
AND (`% Removed-Legal`+ `% Removed-Policy`+ `% Content Not Found`+ `% Content Already Removed`+ `% Not Enough Information`+ `% No Action Taken`) <> 101
AND (`% Removed-Legal`+ `% Removed-Policy`+ `% Content Not Found`+ `% Content Already Removed`+ `% Not Enough Information`+ `% No Action Taken`) <> 99
AND (`% Removed-Legal`+ `% Removed-Policy`+ `% Content Not Found`+ `% Content Already Removed`+ `% Not Enough Information`+ `% No Action Taken`) <> 102
AND (`% Removed-Legal`+ `% Removed-Policy`+ `% Content Not Found`+ `% Content Already Removed`+ `% Not Enough Information`+ `% No Action Taken`) <> 98;

-- Create final aggregated table for visualization
CREATE TABLE Removal_Requests_1 AS
SELECT country, SUM(`Number of Requests`) AS total_requests, SUM(`Items requested to be removed`) AS total_items, 
round(avg(`% Removed-Legal`), 2) AS removed_legal, round(avg(`% Removed-Policy`), 2) AS removed_policy,
round(avg(`% Content Not Found`), 2) AS content_not_found, round(avg(`% Not Enough Information`), 2) AS NOT_enough_information, 
round(avg(`% No Action Taken`), 2) AS no_action_taken, round(avg(`% Content Already Removed`), 2) AS content_already_removed
FROM ggrr_item_perc
GROUP BY country;