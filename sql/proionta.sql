USE farmakeio_db;
SET NAMES utf8mb4;

-- ==========================================================
-- Direct importer (no persistent staging table):
-- Loads CSV into a TEMPORARY table (auto-dropped at session end),
-- then inserts into PROION (superclass) and FARMAKO/PARAFARMAKO.
--
-- CSV path:
--   ./proion_brands.csv
--
-- CSV header expected:
-- eidos,onoma,etairia,katigoria,periektikotita,arx_kostos_temaxiou,
-- elegxomeni_ousia,onoma_drastikis_ousias,systatika
-- ==========================================================

-- 1) TEMPORARY load table (exists only for this session)
DROP TEMPORARY TABLE IF EXISTS tmp_proion_import;
CREATE TEMPORARY TABLE tmp_proion_import (
  import_id               INT AUTO_INCREMENT PRIMARY KEY,
  eidos                   ENUM('FARMAKO','PARAFARMAKO') NOT NULL,
  onoma                   VARCHAR(180) NOT NULL,
  etairia                 VARCHAR(120),
  katigoria               VARCHAR(80),
  periektikotita          FLOAT,
  arx_kostos_temaxiou     DECIMAL(10,2),
  elegxomeni_ousia        TINYINT(1),
  onoma_drastikis_ousias  VARCHAR(120),
  systatika               VARCHAR(255)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- 2) Load CSV (LOCAL INFILE must be enabled in your client)
LOAD DATA LOCAL INFILE './proion_brands.csv'
INTO TABLE tmp_proion_import
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '\\'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(eidos,onoma,etairia,katigoria,
 @periektikotita,@arx_kostos_temaxiou,@elegxomeni_ousia,@onoma_drastikis_ousias,@systatika)
SET
  periektikotita          = NULLIF(@periektikotita,''),
  arx_kostos_temaxiou     = NULLIF(@arx_kostos_temaxiou,''),
  elegxomeni_ousia        = NULLIF(@elegxomeni_ousia,''),
  onoma_drastikis_ousias  = NULLIF(TRIM(TRAILING '\r' FROM @onoma_drastikis_ousias),''),
  systatika               = NULLIF(TRIM(TRAILING '\r' FROM @systatika),'');

-- 3) Import procedure: PROION + subtype + DRASTIKI_OUSIA
DELIMITER //

DROP PROCEDURE IF EXISTS import_proion_brands_direct//
CREATE PROCEDURE import_proion_brands_direct()
BEGIN
  DECLARE done INT DEFAULT 0;

  DECLARE v_eidos  VARCHAR(20);
  DECLARE v_onoma  VARCHAR(180);
  DECLARE v_etairia VARCHAR(120);
  DECLARE v_katigoria VARCHAR(80);
  DECLARE v_periekt FLOAT;
  DECLARE v_kostos DECIMAL(10,2);
  DECLARE v_elegx TINYINT(1);
  DECLARE v_drastiki VARCHAR(120);
  DECLARE v_systatika VARCHAR(255);

  DECLARE v_product_id INT;

  -- For optional ingredient splitting into SYSTATIKA_PARAFARMAKOU
  DECLARE v_rest TEXT;
  DECLARE v_delim CHAR(1);
  DECLARE v_part TEXT;
  DECLARE v_pos INT;

  DECLARE cur CURSOR FOR
    SELECT eidos,onoma,etairia,katigoria,periektikotita,arx_kostos_temaxiou,
           elegxomeni_ousia,onoma_drastikis_ousias,systatika
    FROM tmp_proion_import
    ORDER BY import_id;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  START TRANSACTION;

  OPEN cur;

  read_loop: LOOP
    FETCH cur INTO v_eidos,v_onoma,v_etairia,v_katigoria,v_periekt,v_kostos,
                   v_elegx,v_drastiki,v_systatika;
    IF done = 1 THEN
      LEAVE read_loop;
    END IF;

    -- Always insert into PROION (superclass)
    INSERT INTO PROION (katigoria, etairia, periektikotita, onoma, arx_kostos_temaxiou)
    VALUES (v_katigoria, v_etairia, v_periekt, v_onoma, v_kostos);

    SET v_product_id = LAST_INSERT_ID();

    -- Insert into correct subtype table
    IF v_eidos = 'FARMAKO' THEN

      -- Create DRASTIKI_OUSIA entries for every active substance that appears
      IF v_drastiki IS NOT NULL AND v_drastiki <> '' THEN
        INSERT IGNORE INTO DRASTIKI_OUSIA(onoma) VALUES (v_drastiki);
      END IF;

      -- FARMAKO.onoma_drastikis_ousias is an FK to DRASTIKI_OUSIA.onoma
      INSERT INTO FARMAKO(product_id, elegxomeni_ousia, onoma_drastikis_ousias)
      VALUES (v_product_id, IFNULL(v_elegx,0), NULLIF(v_drastiki,''));

    ELSE

      INSERT INTO PARAFARMAKO(product_id, systatika)
      VALUES (v_product_id, v_systatika);

      -- Optional: also populate SYSTATIKA_PARAFARMAKOU from "systatika"
      IF v_systatika IS NOT NULL AND v_systatika <> '' THEN

        IF INSTR(v_systatika, ';') > 0 THEN
          SET v_delim = ';';
        ELSEIF INSTR(v_systatika, '|') > 0 THEN
          SET v_delim = '|';
        ELSE
          SET v_delim = NULL;
        END IF;

        IF v_delim IS NULL THEN
          INSERT INTO SYSTATIKA_PARAFARMAKOU(product_id, sustatiko)
          VALUES (v_product_id, TRIM(v_systatika));
        ELSE
          SET v_rest = v_systatika;

          split_loop: LOOP
            IF v_rest IS NULL OR v_rest = '' THEN
              LEAVE split_loop;
            END IF;

            SET v_pos = INSTR(v_rest, v_delim);

            IF v_pos = 0 THEN
              SET v_part = TRIM(v_rest);
              SET v_rest = '';
            ELSE
              SET v_part = TRIM(SUBSTRING(v_rest, 1, v_pos - 1));
              SET v_rest = SUBSTRING(v_rest, v_pos + 1);
            END IF;

            IF v_part IS NOT NULL AND v_part <> '' THEN
              INSERT INTO SYSTATIKA_PARAFARMAKOU(product_id, sustatiko)
              VALUES (v_product_id, v_part);
            END IF;
          END LOOP;
        END IF;

      END IF;

    END IF;

  END LOOP;

  CLOSE cur;

  COMMIT;
END//
DELIMITER ;

CALL import_proion_brands_direct();

-- Optional cleanup
DROP PROCEDURE IF EXISTS import_proion_brands_direct;
DROP TEMPORARY TABLE IF EXISTS tmp_proion_import;

-- Add general APOTHIKI
INSERT IGNORE INTO APOTHIKI (storage_id, topothesia)
VALUES (1, 'Earth');

-- Quick checks
SELECT COUNT(*) AS proion_count FROM PROION;
SELECT COUNT(*) AS farmako_count FROM FARMAKO;
SELECT COUNT(*) AS parafarmako_count FROM PARAFARMAKO;
