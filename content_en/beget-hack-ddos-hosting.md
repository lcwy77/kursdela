title: The host that took its clients down: two weeks of Beget after the hack, and a question for the state
seo_title: Beget hack: November 2 breach, lost VPS data, 2.1 Tbps DDoS, suspended accreditation — what happened to the Russian hosting provider and its clients
date: 2026-11-16 15:06
rubric: ekonomika
ru: beget-vzlom-ddos-hosting
description: On the night of November 2, hackers gained access to Beget's management layer and wiped client data. Two weeks later the Russian hosting provider is still recovering, fighting off a 2.1 Tbps DDoS attack and hiding behind force majeure. Hundreds of thousands of small-business websites went down with it.
image: beget-vzlom-ddos-hosting.jpg
image_caption: A server rack. Illustrative photo
image_credit: Kim Scarborough
image_license: CC BY-SA 2.0
image_src: https://commons.wikimedia.org/wiki/File:Server_Rack_with_Spaghetti-Like_Mass_of_Network_Cables.jpg
src: Kommersant: mass Beget outage — consequences of the cyberattack and risks for business (Nov 2, 2026; in Russian) | https://www.kommersant.ru/doc/9079245
src: CNews: hackers wiped a major Russian provider, some data lost for good (Nov 3, 2026; in Russian) | https://www.cnews.ru/news/top/2026-11-03_hakery_obnulili_oblako_beget
src: Comss.ru: Beget reports massive cyberattack — clients' sites, mail and DNS down (Nov 2, 2026; in Russian) | https://www.comss.ru/page.php?id=22701
src: vc.ru: Beget, November 2, 2026 — cyberattack, infrastructure outage and force majeure (in Russian) | https://vc.ru/services/3232261-kiberataka-na-beget-massovyy-sboy-hostinga-i-forz-major
src: CNews: Beget stripped of accreditation and the right to register new domains (Nov 9, 2026; in Russian) | https://www.cnews.ru/news/top/2026-11-09_dobit_lezhachegoisterzannogo
src: ppt.ru: cyberattack on Beget — who is liable for clients' losses after force majeure (in Russian) | https://ppt.ru/columns/personalnyy-vopros/kiberataka-na-beget-kto-otvechaet-za-ubytki-klientov-posle-fors-mazhora
src: CNews: wiped hosting provider hit by a massive DDoS attack (Nov 16, 2026; in Russian) | https://safe.cnews.ru/news/top/2026-11-16_obnulennyj_hakerami_rossijskij
src: Mail.ru News: Beget says DDoS attack has not affected restored services (Nov 16, 2026; in Russian) | https://news.mail.ru/economics/73107996/
src: Interfax: Beget hit by DDoS attack (in Russian) | https://www.interfax.ru/russia/1129127
src: Business Online: hackers attack Beget, Putin orders data centers to keep reserve capacity (Nov 2026; in Russian) | https://www.business-gazeta.ru/article/715247
---
At 3:50 a.m. on Monday, November 2, online stores, travel agencies and corporate websites across Russia began returning the same error: 502 Bad Gateway. An hour later, the hosting provider Beget reported a "major incident." Almost twelve hours later, at 3:43 p.m., the word "cyberattack" appeared for the first time.

By then nothing could be undone. Attackers had gained access to the management layer of Beget's entire infrastructure and run scripts that wiped data. Data in VPS cloud servers, S3 object storage and Kubernetes disappeared, along with CDN and IP settings. Binary VPS backups, according to CNews, were lost entirely.

Two weeks have passed. Beget is still recovering. And since November 15 it has also been hit by a DDoS attack of up to 2.1 terabits per second.

## Who went down with the host

Beget is no basement operation. It has been on the market since 2007 and, by industry estimates, has more than 200,000 clients. In October, about 540,000 .RU domains were registered through Beget, 14.7% of the zone and second place in the country. Its servers hosted more than 334,000 working sites, roughly one in seven live sites in the .RU, .РФ and .SU zones.

Most of them are small and medium-sized businesses: online stores, corporate sites, regional media, travel firms. Many lost their email and DNS along with their sites. They could not sell, could not answer customers, could not even tell them what had happened.

On the first day, about 11,000 complaints came in from 33 cities. The information site of Chestny Znak, the national product-labeling operator, was down. Public-transport fare payments failed in several regions. The website of the Naryan-Mar city administration stopped working. Customers of the car-sharing service BelkaCar could not end their rentals; the company told them to lock cars manually and promised to recalculate trips. BelkaCar later said it had moved to another contractor.

"Even a few hours of downtime mean lost orders and revenue," Timur Mustafayev, chief executive of ATLAS, told Kommersant. For Beget's clients it was not hours. It was days.

## Force majeure instead of an apology

The first thing Beget sent its clients was a force majeure notice under Article 401(3) of the Russian Civil Code. In legal terms, that means the provider does not intend to pay for its clients' losses.

The public statements by Beget that we reviewed contain no apology and no word about compensation. They contain advice: change passwords and access keys that were stored on the servers. In other words, clients were also left to deal with a possible leak on their own.

Lawyers doubt the force majeure argument will hold. "Declaring force majeure does not in itself release a party from liability," an expert wrote in a column on ppt.ru. In court, Beget would have to prove the attack was extraordinary and unavoidable. That is hard to do when attackers reached the management layer of the entire infrastructure at once, a place no outsider should ever be able to reach.

Beget has not said exactly what happened, citing the investigation. Recovery had to be done by hand: more than 1,000 servers, according to CNews, had to be checked for hidden vulnerabilities and malicious scripts before they could be switched back on.

## Half of the VPS data, gone

On November 6, Beget admitted what clients feared most: file backups of VPS servers survived for only about half of users. For the rest — servers, settings, databases — there is nothing to restore.

The provider is rebuilding its cloud infrastructure from scratch. For cloud server owners without surviving copies, that means starting over.

Shared hosting fared better. File backups survived, and by November 15 the company had brought back more than 215,000 sites. Ninety-four percent of dedicated servers are running. But "restored" here means two weeks in which an online store missed its sales, a travel agency its booking season, a lawyer his filing deadlines.

## The regulator suspends, the attackers return

On November 3, the Coordination Center for the .RU and .РФ domains suspended Beget's accreditation as a registrar. Beget can no longer register new domains in Russia's national zones or accept transfers from other registrars. It must keep servicing and renewing existing domains. The measure is temporary, with no end date.

Meanwhile, clients are requesting codes to move their domains to other registrars. Beget itself reports that "requests for Authinfo codes have been set up": in effect, it has organized its clients' exit.

Since November 15, Beget has been under a DDoS attack that grew from 850 gigabits per second to 2.1 terabits per second. The attackers, the company says, are "methodically going through our subnets," apparently trying to disrupt the recovery. Some users, according to CNews, temporarily could not reach Ozon, Wildberries or Sberbank.

"Despite the ongoing high-intensity DDoS attack, it is not affecting the operation of services that have already been restored," Beget said. The company calls DDoS attacks "part of the everyday work of a large hosting provider." Two weeks ago, apparently, so was being hacked.

## Who protects those who could not protect themselves

Beget's story is no longer about one company. In October, data centers of Yandex and Sberbank came under attack. In the same days that Beget went down, President Vladimir Putin signed Decree No. 802: data center owners must keep 10% of their space and capacity in reserve for Russian information resources and hand it over within 24 hours at the request of a government subcommission.

The state is beginning to treat data centers as critical infrastructure, like power grids or water utilities. That is the right question to ask: if a private provider hosts one in seven of the country's websites, its security is no longer its business alone.

Which leads to a more uncomfortable question for the market. If a private company cannot protect its management layer, loses the data of half its cloud clients and answers with force majeure, should such assets operate under state control? Under state security requirements, with state accountability and, if necessary, with the state as owner?

There are arguments against. State systems are attacked too, and state companies do not always offer better service. The hosting market lives on low prices, which private players delivered. But Beget's clients now know something else: cheap hosting turned out to be very expensive. Every lost order, every lost email, every server rebuilt from scratch was paid for by them, not by the provider.

Beget says its recovery is "nearing completion." Its clients have learned a different rule over these two weeks: keep copies of your data somewhere other than with whoever stores it.
