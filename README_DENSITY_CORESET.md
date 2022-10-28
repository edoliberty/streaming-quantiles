
### To generate data do something like this:
```
python make_vectors.py -d 4 -n 1000 > vectors.jsonl
```

### To create a coreset do something like this:
```
cat vectors.jsonl |  python gde.py -d 4 -k 17 > coreset.jsonl
```

The resulting coreset.jsonl file will be a json line separated file that looks likes this
```
{"weight": 1, "vector": [0.4604811325029477, -0.1415783159843467, 1.5942203672298765, -0.12698023729703867]}
{"weight": 1, "vector": [-0.4250542300813231, 2.0036945499901773, -2.248551467099193, -0.47961139567107974]}
{"weight": 2, "vector": [0.42195365231031673, 1.817598207170691, -0.37670168012987754, -0.6838975709136558]}
{"weight": 8, "vector": [0.7840795230701654, -2.086433078266451, -0.9027443737188418, -0.2942541896780809]}
{"weight": 8, "vector": [0.9071054423130541, -0.21492847506617566, -0.24798934478470383, -2.309574167909764]}
...
```
