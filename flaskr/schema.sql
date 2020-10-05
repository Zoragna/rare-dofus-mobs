DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS capture;
DROP TABLE IF EXISTS captureNote;
DROP TABLE IF EXISTS monster;
DROP TABLE IF EXISTS monsterType;

CREATE TABLE user (
  id 		INTEGER PRIMARY KEY AUTOINCREMENT,
  username 	TEXT 	UNIQUE NOT NULL,
  password 	TEXT 	NOT NULL,
  metamob 	TEXT	DEFAULT '',
  admin 	BOOLEAN NOT NULL DEFAULT False
);

CREATE TABLE monster (
  id 		INTEGER PRIMARY KEY AUTOINCREMENT,
  nameFr 	TEXT 	NOT NULL,
  img 		TEXT	DEFAULT '',
  zoneId 	INTEGER NOT NULL,
  monsterType	INTEGER	NOT NULL
);

CREATE TABLE monsterType (
  Type    TEXT		PRIMARY KEY NOT NULL,
  Seq     INTEGER,
  minRes  INTEGER NOT NULL,
  maxRES  INTEGER NOT NULL
);

INSERT INTO monsterType VALUES ('archimonster',1,6,18);
INSERT INTO monsterType VALUES ('notice',2,6,18);
INSERT INTO monsterType VALUES ('cania-bandit',3,3,9);

CREATE TABLE capture (
  id            INTEGER         PRIMARY KEY AUTOINCREMENT,
  monsterId     INTEGER         NOT NULL,
  captured      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  userId        INTEGER         NOT NULL,
  proof         TEXT            DEFAULT '',
  FOREIGN KEY   (monsterId)     REFERENCES      monster(id),
  FOREIGN KEY   (userId)        REFERENCES      user(id)
);

CREATE TABLE captureNote (
  id		INTEGER		PRIMARY KEY AUTOINCREMENT,
  captureId	INTEGER		NOT NULL,
  userId	INTEGER		NOT NULL,
  value		INTEGER		NOT NULL DEFAULT 0,
  FOREIGN KEY	(captureId)	REFERENCES	capture(id),
  FOREIGN KEY	(userId)	REFERENCES	user(id)
);

