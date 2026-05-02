# TODO 
# ogarnąc jak tworzyć dobre query do pubmedu aby dostawac takie badania dietettyczne ? Moze czesc artykulow bedzie maloz wiazana i trudno. dokonczyc caly proces wyszukiwania zeby mozna byloz aczac dzialac z llm najwyzej pozniejbedzie sie to wyszukiwania dopracowyuwac albo artykukly
# https://chatgpt.com/s/t_69f57cce07c08191a7945e3f1b2a6c4c
# Tworze tabele w postgresql pod artykuły
# Łącze sie z api pubmed
# pobieram artykuły 100 co mnie interesuja dla sodium i fiber
# astepnie oddaje stery llmowi zebymmi wyswietlil ich quality score
# tworze ifem podliczenie i zapis do bazy danych jaki ma quality score


# Do zbadania
# Czy sprawdzamy outlinery ?






# Luźne przemyślenia
# DR1DRSTZ 4 oznacza diete oparta na mleku matki więc nalezalloby to usunąć w dalszych analizach


'''
# Opis kolumn DR1TOT_J https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DR1TOT_J.htm#SEQN

SEQN - id uzytkownika
WTDRD1 - Oznacza ile osób w populacji USA reprezentuje dany respondent. 5.397605346934028e-79  jest ich 1063 i to oznacza ze Day 1 dietary recall not done/incomplete.
WTDRD2 - Oznacza ile osób w populacji USA reprezentuje dany respondent.  5.397605346934028e-79 jest ich 1002 i to oznacza ze Day 2 dietary recall not done/incomplete.
DR1DRSTZ - Okreslenie jak wiarygodne jest ich raportowania z dnia zywienia. Czemu jest 1,2 4,5 ? Gdzie 3 ? 4 oznacza diete oparta na mleku matki więc nalezalloby to usunąć w dalszych analizach.
DR1EXMER - identyfikator osoby przeprowadzającej wywiad 
DRABF - Oznaczenie niemowląt które są na diecie mleka matki
DRDINT - oznakowanie z ilu dni były zebrane dane 1 czy 2
DR1DBIH - liczba dni miedzy dniem spozycia (dietary recall) a wywiadem. Ile dni minelo miedzy dniem którego dotyczy dieta a dniem przeprowadzonego wywiadu. Kolumna istnieje zeby okreslic ryzyko błędu pamięci ? Czyli im wieksza wartosc tym mniej wartosciowe dane 
DR1DAY - oznakowanie w jakim dniu jest wspomniana dieta 1-7 Ndz - Sob
DR1LANG - język, którego uzywali respondenci. Tabela na stronie
DR1MRESP - kto głównie odpowiadał na pytania do ankeitowanego poniewaz czesto były wywiady przeprowadzane w domu gdzie była obecna rodzina, lub np respondent nie był ws tanie odpowiedziec na pytanie (np. niemowlę lub bariera jezykowa).  Oznaczenie 1-3 oznacza raczej najbardziej wiarygodne. Tabela na stronie
DR1HELP - kto pomogał przy odpowiedziach. Najczystszy przypadek danych jest 12- No one poniewaz respondent sam odpowiadał bez pomocy. Tabela na stronie
'''


'''
Co zrobiłem

1. Sprawdzam sanity check danych i je oczyszczam jednoczesnie zapoznając sie z kolumnami ogólnymi czyli od SEQN - DR1HELP. Reszta kolumn jest wyspecjalizowana
2. WTDRD1 widze ze ma wartość przy niektórych  5.397605346934028e-79 co oznacza bliską zeru. Widze tez zaleznosc ze te same jednostki WTDR2D maja missing value
3. Tworze warstwe silver gdzie będę miał wstępnie ustrykturyzowane dane według siebie
4. Tworze docker-compose z postgresql i zapisuje warstwe silver do niego
5. Przechodzę do warstwy gold
6. Następnie zajmuje sie pobieraniem badan z pubmed. Zastanawiam siejak tworzyc prawidłowe zapytania aby publikacje które pobiore były jak najblizsze zywieniu
'''