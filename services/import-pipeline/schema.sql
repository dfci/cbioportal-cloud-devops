CREATE TABLE IF NOT EXISTS files
(
  id           INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  content_hash VARCHAR(64)                       NOT NULL,
  path         TEXT                              NOT NULL
)
;

CREATE UNIQUE INDEX IF NOT EXISTS file_data_id_uindex
  ON files (id)
;

CREATE UNIQUE INDEX IF NOT EXISTS file_data_content_hash_uindex
  ON files (content_hash)
;

CREATE TABLE IF NOT EXISTS orgs
(
  id       INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  org_name TEXT                              NOT NULL

)
;

CREATE TABLE IF NOT EXISTS studies
(
  id         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  org_id     INTEGER                           NOT NULL,
  study_name TEXT                              NOT NULL,
  available  BOOLEAN,
  CONSTRAINT studies_org_id_fk FOREIGN KEY (org_id) REFERENCES orgs (id)

)
;

CREATE UNIQUE INDEX IF NOT EXISTS studies_id_uindex
  ON studies (id)
;

CREATE UNIQUE INDEX IF NOT EXISTS studies_study_name_uindex
  ON studies (org_id, study_name)
;

CREATE TABLE IF NOT EXISTS study_versions
(
  id                 INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  study_id           INT                               NOT NULL,
  aggregate_hash     VARCHAR(64)                       NOT NULL,
  passes_validation  BOOLEAN,
  loads_successfully BOOLEAN,
  currently_loaded   BOOLEAN,
  CONSTRAINT study_versions_studies_id_fk FOREIGN KEY (study_id) REFERENCES studies (id)
)
;

CREATE UNIQUE INDEX IF NOT EXISTS study_versions_id_uindex
  ON study_versions (id)
;

CREATE TABLE IF NOT EXISTS study_version_files
(
  study_version_id   INTEGER NOT NULL,
  file_id            INTEGER NOT NULL,
  file_path          TEXT    NOT NULL,
  file_modified_date VARCHAR(19),
  PRIMARY KEY (study_version_id, file_id),
  CONSTRAINT study_version_files_study_versions_id_fk FOREIGN KEY (study_version_id) REFERENCES study_versions (id),
  CONSTRAINT study_version_files_files_id_fk FOREIGN KEY (file_id) REFERENCES files (id)
)
;

CREATE UNIQUE INDEX IF NOT EXISTS study_version_files_file_path_uindex
  ON study_version_files (study_version_id, file_path)
;

CREATE UNIQUE INDEX IF NOT EXISTS study_version_files_study_version_id_file_id_file_path_uindex
  ON study_version_files (study_version_id, file_id, file_path)
;

CREATE TABLE IF NOT EXISTS study_version_validation
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    study_version_id INT NOT NULL,
    status_code INT,
    success BOOLEAN NOT NULL,
    output TEXT,
    time_added INT,
    CONSTRAINT study_version_validation_study_versions_id_fk FOREIGN KEY (study_version_id) REFERENCES study_versions (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS study_version_validation_id_uindex ON study_version_validation (id);