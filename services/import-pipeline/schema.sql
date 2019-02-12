CREATE TABLE IF NOT EXISTS files
(
  id           INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  content_hash VARCHAR(64)                       NOT NULL,
  path         TEXT                              NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS file_data_id_uindex
  ON files (id);

CREATE UNIQUE INDEX IF NOT EXISTS file_data_content_hash_uindex
  ON files (content_hash);

CREATE TABLE IF NOT EXISTS orgs
(
  id       INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  org_name TEXT                              NOT NULL

);

CREATE TABLE IF NOT EXISTS studies
(
  id         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  org_id     INTEGER                           NOT NULL,
  study_name TEXT                              NOT NULL,
  available  BOOLEAN,
  CONSTRAINT studies_org_id_fk FOREIGN KEY (org_id) REFERENCES orgs (id)

);

CREATE UNIQUE INDEX IF NOT EXISTS studies_id_uindex
  ON studies (id);

CREATE UNIQUE INDEX IF NOT EXISTS studies_study_name_uindex
  ON studies (org_id, study_name);

CREATE TABLE IF NOT EXISTS study_access
(
  id                 INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  study_id           INT                               NOT NULL,
  file_id            INT                               NOT NULL,
  CONSTRAINT study_access_studies_id_fk FOREIGN KEY (study_id) REFERENCES studies (id),
  CONSTRAINT study_access_files_id_fk FOREIGN KEY (file_ID) REFERENCES files (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS study_access_id_uindex ON study_access(id);

CREATE TABLE IF NOT EXISTS study_versions
(
  id                 INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  study_id           INT                               NOT NULL,
  aggregate_hash     VARCHAR(64)                       NOT NULL,
  passes_validation  BOOLEAN,
  loads_successfully BOOLEAN,
  currently_loaded   BOOLEAN,
  CONSTRAINT study_versions_studies_id_fk FOREIGN KEY (study_id) REFERENCES studies (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS study_versions_id_uindex
  ON study_versions (id);

CREATE TABLE IF NOT EXISTS study_version_files
(
  study_version_id   INTEGER NOT NULL,
  file_id            INTEGER NOT NULL,
  file_path          TEXT    NOT NULL,
  file_modified_date VARCHAR(19),
  PRIMARY KEY (study_version_id, file_id),
  CONSTRAINT study_version_files_study_versions_id_fk FOREIGN KEY (study_version_id) REFERENCES study_versions (id),
  CONSTRAINT study_version_files_files_id_fk FOREIGN KEY (file_id) REFERENCES files (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS study_version_files_file_path_uindex
  ON study_version_files (study_version_id, file_path);

CREATE UNIQUE INDEX IF NOT EXISTS study_version_files_study_version_id_file_id_file_path_uindex
  ON study_version_files (study_version_id, file_id, file_path);

CREATE TABLE IF NOT EXISTS study_version_validation
(
  id               INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  study_version_id INT                               NOT NULL,
  status_code      INT,
  success          BOOLEAN                           NOT NULL,
  output           TEXT,
  time_added       INT,
  CONSTRAINT study_version_validation_study_versions_id_fk FOREIGN KEY (study_version_id) REFERENCES study_versions (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS study_version_validation_id_uindex
  ON study_version_validation (id);

CREATE TABLE IF NOT EXISTS study_version_import
(
  id               INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  study_version_id INT                               NOT NULL
    CONSTRAINT study_version_import_study_versions_id_fk
    REFERENCES study_versions,
  status_code      INT,
  success          BOOLEAN                           NOT NULL,
  output           TEXT,
  time_added       INT
);

CREATE UNIQUE INDEX IF NOT EXISTS study_version_import_id_uindex
  ON study_version_import (id);
CREATE VIEW IF NOT EXISTS top_level_dashboard AS
  WITH
      _version_status AS (SELECT o.id                 org_id,
                                 o.org_name,
                                 s.id                 study_id,
                                 s.study_name,
                                 s.available,
                                 v.id                 study_version_id,
                                 row_number()         OVER (PARTITION BY s.id ORDER BY v.id DESC) _id,
                                 v.passes_validation  current_version_passes_validation,
                                 v.loads_successfully current_version_loads_successfully,
                                 v.currently_loaded   current_version_loaded
                          FROM orgs o
                                 INNER JOIN studies s ON o.id = s.org_id
                                 INNER JOIN study_versions v ON s.id = v.study_id),
      most_recent_version_status AS (SELECT *
                                     FROM _version_status
                                     WHERE _id = 1),
      historical_version_status AS (SELECT s.id s_id, sv.currently_loaded
                                    FROM studies s
                                           LEFT JOIN study_versions sv ON (s.id = sv.study_id) AND sv.currently_loaded
                                    WHERE sv.id IN (SELECT study_version_id FROM _version_status WHERE _id != 1
                                                                                                   AND current_version_loaded))
  SELECT m.*,
         CASE
           WHEN m.current_version_loaded AND h.currently_loaded IS NOT NULL THEN FALSE
           ELSE h.currently_loaded END previous_version_loaded
  FROM most_recent_version_status m
         LEFT JOIN historical_version_status h ON h.s_id = m.study_id
  ORDER BY org_id DESC, study_id DESC, study_version_id DESC;

CREATE VIEW IF NOT EXISTS second_level_dashboard AS
  WITH
      _i AS (SELECT *, row_number() OVER (PARTITION BY study_version_id ORDER BY id DESC) _id
             FROM study_version_import)
  SELECT sv.id           study_version_id,
         sv.study_id,
         sv.passes_validation,
         sv.loads_successfully,
         sv.currently_loaded,
         v.id            validation_id,
         v.success       validation_success,
         v.status_code   validation_status_code,
         v.time_added    validation_time_added,
         svi.id          import_id,
         svi.success     import_success,
         svi.status_code import_status_code,
         svi.time_added  import_time_added
  FROM study_versions sv
         INNER JOIN study_version_validation v ON sv.id = v.study_version_id
         LEFT JOIN _i svi ON sv.id = svi.study_version_id

  WHERE svi._id = 1
     OR svi._id IS NULL
  ORDER BY sv.study_id DESC, sv.id DESC;

