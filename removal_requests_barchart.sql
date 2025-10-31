-- Rename table for easier reference
RENAME TABLE google_government_removal_requests TO ggrr_item_perc;

-- Create table with weighted averages for removal request outcomes
CREATE TABLE request_outcome_perc AS
SELECT
  `Country`, SUM(`Number of Requests`) AS 'Total Requests',
  -- Weighted avg of "% Removed-Legal"
  ROUND(
    SUM(
      CASE
        WHEN `% Removed-Legal` IS NOT NULL AND `Number of Requests` > 0
        THEN `Number of Requests` * `% Removed-Legal`
        ELSE 0
      END
    )
    / NULLIF(
        SUM(
          CASE WHEN `% Removed-Legal` IS NOT NULL AND `Number of Requests` > 0
          THEN `Number of Requests` ELSE 0 END
        ), 0
      )
  , 2) AS `% Removed-Legal`,
  -- Weighted avg of "% Removed-Policy"
  ROUND(
    SUM(
      CASE
        WHEN `% Removed-Policy` IS NOT NULL AND `Number of Requests` > 0
        THEN `Number of Requests` * `% Removed-Policy`
        ELSE 0
      END
    )
    / NULLIF(
        SUM(
          CASE WHEN `% Removed-Policy` IS NOT NULL AND `Number of Requests` > 0
          THEN `Number of Requests` ELSE 0 END
        ), 0
      )
  , 2) AS `% Removed-Policy`,
  -- Weighted avg of "% Content Not Found"
  ROUND(
    SUM(
      CASE
        WHEN `% Content Not Found` IS NOT NULL AND `Number of Requests` > 0
        THEN `Number of Requests` * `% Content Not Found`
        ELSE 0
      END
    )
    / NULLIF(
        SUM(
          CASE WHEN `% Content Not Found` IS NOT NULL AND `Number of Requests` > 0
          THEN `Number of Requests` ELSE 0 END
        ), 0
      )
  , 2) AS `% Content Not Found`,
  -- Weighted avg of "% Not Enough Information"
  ROUND(
    SUM(
      CASE
        WHEN `% Not Enough Information` IS NOT NULL AND `Number of Requests` > 0
        THEN `Number of Requests` * `% Not Enough Information`
        ELSE 0
      END
    )
    / NULLIF(
        SUM(
          CASE WHEN `% Not Enough Information` IS NOT NULL AND `Number of Requests` > 0
          THEN `Number of Requests` ELSE 0 END
        ), 0
      )
  , 2) AS `% Not Enough Information`,
  -- Weighted avg of "% No Action Taken"
  ROUND(
    SUM(
      CASE
        WHEN `% No Action Taken` IS NOT NULL AND `Number of Requests` > 0
        THEN `Number of Requests` * `% No Action Taken`
        ELSE 0
      END
    )
    / NULLIF(
        SUM(
          CASE WHEN `% No Action Taken` IS NOT NULL AND `Number of Requests` > 0
          THEN `Number of Requests` ELSE 0 END
        ), 0
      )
  , 2) AS `% No Action Taken`,
  -- Weighted avg of "% Content Already Removed"
  ROUND(
    SUM(
      CASE
        WHEN `% Content Already Removed` IS NOT NULL AND `Number of Requests` > 0
        THEN `Number of Requests` * `% Content Already Removed`
        ELSE 0
      END
    )
    / NULLIF(
        SUM(
          CASE WHEN `% Content Already Removed` IS NOT NULL AND `Number of Requests` > 0
          THEN `Number of Requests` ELSE 0 END
        ), 0
      )
  , 2) AS `% Content Already Removed`
FROM ggrr_item_perc
GROUP BY `Country`
ORDER BY `Total Requests` desc;

-- Data quality check: validate that percentage columns sum to approximately 100%
SELECT count(*) FROM request_outcome_perc
WHERE (`% Removed-Legal` + `% Removed-Policy` + `% Content Not Found` + `% Not Enough Information` + `% No Action Taken` + `% Content Already Removed`) > 101
UNION ALL
SELECT count(*) FROM request_outcome_perc
WHERE (`% Removed-Legal` + `% Removed-Policy` + `% Content Not Found` + `% Not Enough Information` + `% No Action Taken` + `% Content Already Removed`) < 99;