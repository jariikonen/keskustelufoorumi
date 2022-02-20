INSERT INTO topics (topic, description)
VALUES (
    'Yleinen keskustelualue',
    'Kaikille avoin keskustelualue, jossa voi keskustella yleisistä aiheista.'
);

INSERT INTO topics (topic, description)
VALUES (
    'Rajoitettu keskustelualue',
    'Rajoitettu keskustelualue, jota kaikki voivat lukea, mutta jolle vain ryhmän jäsenet (sekä ylläpitäjät ja pääkäyttäjät) voivat kirjoittaa.'
);

INSERT INTO topics (topic, description)
VALUES (
    'Suljettu keskustelualue',
    'Suljettu keskustelualue, jolla ryhmän jäsenet voivat keskustella luottamuksellisesti. Toisin sanottuna kaikki voivat tietää ryhmän olemassaolosta, mutta vain ryhmän jäsenet (sekä ylläpitäjät ja pääkäyttäjät) voivat lukea tai kirjoittaa.'
);

INSERT INTO topics (topic, description)
VALUES (
    'Salainen keskustelualue',
    'Salainen keskustelualue, jolla salaseuran sisäpiiri voi keskustella salaisista asioista. Keskustelualue näkyy vain ryhmän jäsenille (sekä ylläpitäjille ja pääkäyttäjille).'
);

INSERT INTO groups (group_name) VALUES ('Yleinen keskustelualue');
INSERT INTO groups (group_name) VALUES ('Rajoitettu keskustelualue');
INSERT INTO groups (group_name) VALUES ('Suljettu keskustelualue');
INSERT INTO groups (group_name) VALUES ('Salainen keskustelualue');

/* Yleinen keskustelualue - ALL */
INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
VALUES (3, 1, true, true, true);

/* Rajoitettu keskustelualue - ALL */
INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
VALUES (3, 2, true, true, false);
/* Rajoitettu keskustelualue - Rajoitettu keskustelualue */
INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
VALUES (5, 2, true, true, true);

/* Suljettu keskustelualue - ALL */
INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
VALUES (3, 3, true, false, false);
/* Suljettu keskustelualue - Suljettu keskustelualue */
INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
VALUES (6, 3, true, true, true);

/* Salainen keskustelualue - Salainen keskustelualue */
INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
VALUES (7, 4, true, true, true);
