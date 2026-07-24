-- ============================================================
-- Indian Medicine Price Gap — analytical SQL queries
-- Table: medicines (one row per medicine, cleaned + per-unit priced)
-- ============================================================

-- Q1. Dataset overview by formulation type
SELECT pack_type,
       COUNT(*)                               AS medicines,
       ROUND(AVG(price_per_unit), 2)          AS avg_ppu,
       ROUND(MEDIAN(price_per_unit), 2)       AS median_ppu
FROM medicines
GROUP BY pack_type ORDER BY medicines DESC;

-- Q2. Biggest price gaps: composition+formulation with >= 30 brands,
--     ranked by (costliest per-unit / cheapest per-unit)
WITH stats AS (
    SELECT comp_and_type,
           COUNT(*)                                        AS brand_count,
           MIN(price_per_unit)                             AS min_ppu,
           MAX(price_per_unit)                             AS max_ppu,
           ROUND(MEDIAN(price_per_unit), 3)                AS median_ppu
    FROM medicines
    WHERE price_per_unit > 0
    GROUP BY comp_and_type
    HAVING brand_count >= 30 AND min_ppu > 0
)
SELECT comp_and_type, brand_count,
       ROUND(min_ppu, 3) AS min_ppu, ROUND(max_ppu, 2) AS max_ppu,
       ROUND(max_ppu / min_ppu, 1) AS price_ratio
FROM stats ORDER BY price_ratio DESC LIMIT 20;

-- Q3. The competition paradox: median price gap by number of competing brands
WITH stats AS (
    SELECT comp_and_type, COUNT(*) AS brand_count,
           MAX(price_per_unit) / MIN(price_per_unit) AS price_ratio
    FROM medicines WHERE price_per_unit > 0
    GROUP BY comp_and_type HAVING brand_count >= 5 AND MIN(price_per_unit) > 0
)
SELECT CASE
         WHEN brand_count BETWEEN 5 AND 10   THEN '5-10'
         WHEN brand_count BETWEEN 11 AND 25  THEN '11-25'
         WHEN brand_count BETWEEN 26 AND 50  THEN '26-50'
         WHEN brand_count BETWEEN 51 AND 100 THEN '51-100'
         WHEN brand_count BETWEEN 101 AND 500 THEN '101-500'
         ELSE '500+' END                                   AS brand_bin,
       COUNT(*)                                            AS compositions,
       ROUND(MEDIAN(price_ratio), 1)                       AS median_price_ratio
FROM stats
GROUP BY brand_bin
ORDER BY CASE brand_bin WHEN '5-10' THEN 1 WHEN '11-25' THEN 2 WHEN '26-50' THEN 3
         WHEN '51-100' THEN 4 WHEN '101-500' THEN 5 ELSE 6 END;

-- Q4. Affordability: how many medicines are overpriced vs the cheapest alternative
SELECT ROUND(100.0 * SUM(CASE WHEN affordability_index > 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_2x,
       ROUND(100.0 * SUM(CASE WHEN affordability_index > 5 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_5x,
       ROUND(100.0 * SUM(CASE WHEN affordability_index > 10 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_10x
FROM medicines;

-- Q5. Most overpriced manufacturers (avg per-unit premium vs composition median, min 50 products)
SELECT manufacturer_name,
       COUNT(*)                          AS products,
       ROUND(AVG(premium_ratio), 2)      AS avg_premium,
       ROUND(AVG(price_per_unit), 2)     AS avg_ppu
FROM medicines
GROUP BY manufacturer_name HAVING products >= 50
ORDER BY avg_premium DESC LIMIT 15;

-- Q6. Most affordable manufacturers (lowest premium, min 50 products)
SELECT manufacturer_name,
       COUNT(*)                          AS products,
       ROUND(AVG(premium_ratio), 2)      AS avg_premium
FROM medicines
GROUP BY manufacturer_name HAVING products >= 50
ORDER BY avg_premium ASC LIMIT 15;

-- Q7. Price gap by therapeutic category (median ratio over compositions with >= 10 brands)
WITH stats AS (
    SELECT comp_and_type, therapy_category, COUNT(*) AS brand_count,
           MAX(price_per_unit) / MIN(price_per_unit) AS price_ratio
    FROM medicines WHERE price_per_unit > 0
    GROUP BY comp_and_type HAVING brand_count >= 10 AND MIN(price_per_unit) > 0
)
SELECT therapy_category,
       COUNT(*)                        AS compositions,
       ROUND(MEDIAN(price_ratio), 1)   AS median_price_ratio
FROM stats GROUP BY therapy_category ORDER BY median_price_ratio DESC;

-- Q8. Most crowded molecules (composition with the most competing brands)
SELECT full_composition,
       COUNT(*)                         AS brands,
       ROUND(MIN(price_per_unit), 3)    AS cheapest_ppu,
       ROUND(MAX(price_per_unit), 2)    AS costliest_ppu
FROM medicines
GROUP BY full_composition ORDER BY brands DESC LIMIT 15;

-- Q9. Single-ingredient vs combination drug pricing
SELECT CASE WHEN is_combination_drug = 1 THEN 'Combination' ELSE 'Single-ingredient' END AS drug_kind,
       COUNT(*)                          AS medicines,
       ROUND(MEDIAN(price_per_unit), 2)  AS median_ppu
FROM medicines GROUP BY is_combination_drug;

-- Q10. The most expensive medicines (premium segment)
SELECT name, manufacturer_name, salt_name, pack_type,
       ROUND(price, 0) AS price, ROUND(price_per_unit, 2) AS ppu
FROM medicines ORDER BY price DESC LIMIT 15;

-- Q11. Cheapest vs costliest brand for common household molecules (savings)
WITH commons AS (
    SELECT * FROM medicines
    WHERE lower(salt_name) IN ('paracetamol','cetirizine','omeprazole','metformin',
        'atorvastatin','azithromycin','amoxycillin','pantoprazole','amlodipine','telmisartan')
)
SELECT salt_name,
       COUNT(*)                          AS brands,
       ROUND(MIN(price_per_unit), 3)     AS cheapest_ppu,
       ROUND(MAX(price_per_unit), 2)     AS costliest_ppu,
       ROUND(MAX(price_per_unit) - MIN(price_per_unit), 2) AS saving_per_unit
FROM commons GROUP BY salt_name ORDER BY saving_per_unit DESC;
