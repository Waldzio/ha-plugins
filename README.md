# Ping Logger Home Assistant Add-on (Waldi Edition)

Loguje ping wybranych adresów IP, publikuje sensory przez MQTT do Home Assistant.
Konfiguracja: przez GUI, podajesz adresy IP, interwał, dni logowania, login/hasło MQTT (użytkownik HA).
Każdy adres IP to osobny sensor.
Wysyła wartość tylko przy zmianie (zaokrąglenie do ms).
MQTT discovery działa automatycznie.

Instrukcja instalacji:
1. Skopiuj katalog `ping_logger` i plik `repository.json` do katalogu repozytorium dodatków Home Assistant.
2. Dodaj repo do HA jako niestandardowe repozytorium.
3. W GUI ustaw login/hasło MQTT (użytkownik Home Assistanta).
4. Gotowe!