### Zu Nodes, Defense Strategien (und Attack Actions): Wie ist bei Nodes der `compromised`‑Wert zu verstehen? Warum nutzen Verteidiger (z.B. in der reactive defense strategy) `compromised` direkt, statt erst zu wissen, dass ein Knoten kompromittiert ist, nachdem die Detection den Angriff bemerkt hat?

Das ist ein Bug von den Anfängen des Projektes. Der reactive Defender darf das compromised nicht direkt bekommen (oder zumindest nicht zu Entscheidungszwecken.)


### Was ist das Datenmodell, das hinter einer Node steht? Wie werden Services genutzt? Was ist der Sinn hinter all den Properties, die in den Beispielnetzwerken hinterlegt sind?

Ich denke Sachen wie id, software, assets, compromised, access, properties, exposed_to_internet sind klar. Services, exposed services und capabilites sind gerade basically dead code. Auch iwann eingebaut weil ich dachte es könnte sinnvoll sein und dann nie benutzt.
Same mit den Properties. Wenn ihr etwas davon sinnvoll findet könnt ihr es behalten, bzw. in zukünftigen Actions implementieren. Gerade werden nur: Exposed_to_internet, endpoint_protection, rdp und ssh genutzt.


### Warum wird den Funktionen zur "Damageberechnung" einer Attack‑Action eine Angreifer‑ID übergeben?

Wird gerade nicht benutzt und ist auch nicht nötig, denke ich, außer man wolle implementieren das verschiedene Angreifer verschieden viel damage machen, bei gleichen Restbedingungen.


### Was ist der Sinn des EventTypes `STATE_CHANGE`?

Auch ein Artefakt. War mal ein allgemeiner State_Change der alle nicht spezifizierten Events gesammelt hat. Kann entfernt werden.


### Allgemein: Was passiert, nachdem ein Event "gepublished" wurde? Wird das nur zu Historien‑Zwecken getan?

Da war ich in meiner Design Pattern Phase. Das ist basically nur eine super overengineerter HistoryRecorder. Alles wichtige wird im heapq gemanaged. Könnte man natürlich actually benutzen oder komplett reduzieren auf einen HistoryLogger, aber wenn ihr den einfach so lasst ist das auch fine ig.


### Was ist der Sinn vom `SimulationObserver`?

Wird gerade auch nicht genutzt. (Auch Teil des Sub-Pub-ObserverPatterns)

### Wie genau soll der `network_state` in der `choose_action`‑Methode der Actors genutzt werden? Aktuell scheint er nicht wirklich genutzt zu werden — Attacker nutzen beispielsweise nur die `visible_nodes`.

Gar nicht. network_state ist basically nochmal das network object. Kann entfernt werden. (Angreifer nutzen es nicht) Beim Defender kann es einfach durch `defender.simulator.network` ersetzt werden. Ansonsten drinnen lassen. (Darf dann natürlich nicht von einem Attacker für das decision-making genutzt werden.)

### Was war für den `Economic Impact`‑Abschnitt in den Model Results geplant? Lohnt es sich, dieses Feature weiter zu verfolgen?

Dort sollten für jeden einzelnen Akteur gezeigt werden, wieviel damage, gain, cost gemacht wurde, one-off oder time-acc. Wenn ihr immer nur mit einem attacker (bzw. einer attacker gruppe [die wird auch über einen Actor simuliert]) und defender arbeitet, lohnt sich das nicht. Wenn es um 2 Akteur(gruppen) geht die gegeneinander auf einem Network competen ist es vielleicht ganz lustig, aber definitiv keine prio.
