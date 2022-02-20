# Keskustelufoorumi

Aineopintojen harjoitustyö: Tietokantasovellus, kevät 2022.

## Harjoitustyön aihe: keskustelufoorumi

Projektin aiheena on kurssin esimerkkisovelluksissa kuvatun kaltainen keskustelusovellus. Sovelluksessa voidaan käydä keskusteluja useilla keskustelualueilla, joilla kullakin voi olla useita viestiketjuja. Jokainen käyttäjä on peruskäyttäjä tai ylläpitäjä.

Sovelluksen toiminnallisuuksia (alustava lista):

* Käyttäjä voi luoda itselleen tunnuksen ja kirjautua sillä sisään ja ulos. (**toteutettu**)
* Käyttäjä näkee sovelluksen aloitusnäkymässä listan ylläpitäjien lisäämistä keskustelualueista sekä jokaisen alueen ketjujen ja viestien määrän ja viimeksi lähetetyn viestin ajankohdan. Käyttäjän ei tarvitse olla kirjautunut sisään nähdäkseen listan. (**toteutettu**)
* Käyttäjä näkee listan keskustelualueen viestiketjujen otsikoista, niillä olevien viestien määristä ja viimeksi lähetettyjen viestien ajankohdista, klikkaamalla keskustelualueen otsikkoa. (**toteutettu**)
* Käyttäjä voi lukea viestiketjun viestit klikkaamalla viestiketjun otsikkoa. (**toteutettu**)
* Käyttäjä voi (kirjauduttuaan sisään) luoda keskustelualueelle uuden ketjun antamalla ketjun otsikon ja aloitusviestin sisällön. (**toteutettu**)
* Käyttäjä voi (kirjauduttuaan sisään) kirjoittaa uuden viestin olemassa olevaan ketjuun. (**toteutettu**)
* Käyttäjä voi (kirjauduttuaan sisään) muokata luomansa ketjun otsikkoa sekä lähettämänsä viestin sisältöä (**toteutettu**). Käyttäjä voi myös poistaa ketjun tai viestin (*tämä vielä toteuttamatta*).
* Käyttäjä voi etsiä kaikki viestit, joiden osana on annettu sana. (*vielä toteuttamatta*)
* Ylläpitäjä voi lisätä ja poistaa keskustelualueita. (**toteutettu**)
* Ylläpitäjä voi luoda salaisen alueen ja määrittää, keillä käyttäjillä on pääsy alueelle. (**toteutettu osittain**; toiminnallisuuden mahdollistavat käyttöoikeusrakenteet (käyttäjäroolit ja keskustelualueisiin liitettävät käyttöoikeudet) on toteutettu, mutta ylläpitäjä ei voi vielä muokata lisättävän keskustelualueen käyttöoikeuksia)

## Välipalautus 2

Sovelluksen keskeiset toiminnallisuudet on toteutettu, mutta toteuttamattomiakin vielä on. Merkitsin toteutetut toiminnot yllä olevaan listaan toiminnallisuuksista.

Sovellusta voi testata Herokussa osoitteessa https://mysterious-ravine-44883.herokuapp.com/.

Huom! Aihealueiden lisääminen löytyy hallintasivulta.

## Välipalautus 3

Alkuperäisestä toiminnallisuuslistasta on vielä toteuttamatta viestien ja ketjujen poistaminen, hakutoiminto ja keskustelualueen näkyvyyden / käyttöoikeuksien asettaminen. Lisäksi sovellukseen on tarkoitus toteuttaa mahdollisuus katsella ja muokata omia käyttäjätietoja sekä toteuttaa hallintapaneelin laajemmat keskustelualuiden ja käyttäjätilien hallintaominaisuudet.

Toteutin sovellukseen käyttöoikeusjärjestelmän, jossa on kolme käyttäjäroolia: käyttäjä (user), ylläpitä (admin) ja pääkäyttäjä (super). Lisäksi keskustelualueisiin liittyy kaksi ryhmää ALL (kaikki käyttäjät) ja keskustelualueen mukaan nimetty ryhmä keskustelualueen etuoikeutetuille käyttäjille. Näille ryhmille voidaan antaa seuraavat kolme oikeutta: oikeus tietää ryhmän olemassaolosta (know), lukuoikeus (read) ja kirjoitusoikeus (write).

Lopulliseen sovellukseen on tarkoitus toteuttaa vielä mahdollisuuksien mukaan seuraavia toiminnallisuuksia:

* Käyttäjät (user) voivat poistaa kirjoittamansa viestit. Tällöin viestin sisältö tyhjennetään ja viestin tietoihin asetetaan poistettu lippu. Tämän jälkeen viesti näkyy listauksissa poistettuna (ts. sen tiedoissa lukee 'poistettu').
* Käyttäjät voivat vaihtaa oman käyttäjätunnuksensa ja salasanansa.
* Käyttäjät voivat poistaa omat tietonsa (käyttäjätunnus ja salasana) järjestelmästä. Jos järjestelmässä on edelleen käyttäjän kirjoittamia viestejä, poistamisesta seuraa, että käyttäjän tietoihin tehdään merkintä tilin poistosta, jonka jälkeen tilille ei voi enää kirjautua. (Jos järjestelmässä olisi käyttäjästä henkilökohtaisia tietoja, nämä tietenkin poistettaisiin samalla.) Jos käyttäjän kirjoittamia viestejä ei ole, poistetaan käyttäjätunnus kokonaan järjestelmästä.
* Ylläpitäjät (admin) voivat poistaa mitä tahansa viestejä siten, että niiden 'poistettu'-lippu nostetaan, mutta viestin sisältöä ei poisteta. Viestit näytetään tällöin listauksissa poistettuina.
* Ylläpitäjät voivat poistaa kokonaisen viestiketjun tai keskustelualueen siten, että viestit asetetaan poistetuiksi, mutta niitä ei poisteta tietokannasta. Ketju asetetaan tällöin myös käyttäjille näkymättömäksi.
* Ylläpitäjät (ja pääkäyttäjät) voivat jäädyttää ketjun / keskustelualueen siten, että sille ei voi kirjoittaa uusia viestejä, eikä sillä olevia viestejä voi muokata.
* Ylläpitäjät (ja pääkäyttäjät) voivat vaihtaa käyttäjän salasanan.
* Ylläpitäjät voivat korottaa käyttäjän ylläpitäjäksi.
* Ylläpitäjät voivat poistaa käyttäjän siten, että tili asetetaan poistetuksi, mutta tietoja ei poisteta.
* Pääkäyttäjät voivat poistaa viestiketjun tai keskustelualueen kokonaan siten, että viestit poistetaan kokonaan tietokannasta.
* Pääkäyttäjät voivat poistaa käyttäjiä siten, että tiedot poistetaan myös tietokannasta. Tällöin käyttäjällä ei kuitenkaan saa olla viestejä tietokannassa.
* Pääkäyttäjät voivat tehdä käyttäjistä ja ylläpitäjistä pääkäyttäjiä.
* Pääkäyttäjät voivat poistaa ylläpitäjiä.

Sovellusta voi edelleen testata Herokussa osoitteessa https://mysterious-ravine-44883.herokuapp.com/.

Huom! Järjestelmässä on valmiina kaksi tiliä ylläpitäjä (tunnus:admin, salasana: 12345) ja pääkäyttäjä (tunnus: super, salasana: 12345).