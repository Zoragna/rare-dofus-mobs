DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS capture;
DROP TABLE IF EXISTS captureNote;
DROP TABLE IF EXISTS monster;
DROP TABLE IF EXISTS monsterType;

CREATE TABLE account (
  id 		SERIAL	PRIMARY KEY,
  username 	TEXT 	UNIQUE NOT NULL,
  password 	TEXT 	NOT NULL,
  metamob 	TEXT	DEFAULT '',
  admin 	BOOLEAN NOT NULL DEFAULT False
);

CREATE TABLE monster (
  id 		SERIAL	PRIMARY KEY,
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
  id            SERIAL 	        PRIMARY KEY,
  monsterId     INTEGER         NOT NULL,
  captured      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  userId        INTEGER         NOT NULL,
  proof         TEXT            DEFAULT '',
  FOREIGN KEY   (monsterId)     REFERENCES      monster(id),
  FOREIGN KEY   (userId)        REFERENCES      account(id)
);

CREATE TABLE captureNote (
  id		SERIAL		PRIMARY KEY,
  captureId	INTEGER		NOT NULL,
  userId	INTEGER		NOT NULL,
  value		INTEGER		NOT NULL DEFAULT 0,
  FOREIGN KEY	(captureId)	REFERENCES	capture(id),
  FOREIGN KEY	(userId)	REFERENCES	account(id)
);

