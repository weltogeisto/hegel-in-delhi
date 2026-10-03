# The map

`lutyens.json` is the map of Hegel's quarter of Delhi that the page draws. It is **derived from OpenStreetMap**.

> Map data © OpenStreetMap contributors, available under the [Open Database License 1.0 (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).
> See <https://www.openstreetmap.org/copyright>. The page shows this attribution under the map.

The file is a *derived database* in the sense of the ODbL: it is OSM data rasterised onto a tile grid, with a few
additions marked below. It is offered under the same licence (ODbL 1.0); the page and its code are not part of it.

## What is in it

A window of 2.98 x 2.11 km, lat 28.5855 to 28.6045, lon 77.1995 to 77.2300 (Tughlak Road, Lodhi Gardens, Khan Market,
Safdarjung's Tomb, Gandhi Smriti, the Gymkhana, the IIC), as a grid of 249 x 177 tiles of 12 m (equirectangular,
x scaled by cos of the latitude, origin at the north-west corner, y pointing south).

| key | what |
|---|---|
| `ground` | the terrain class of every tile, run-length encoded `[class, run, ...]`, row by row (`classes` names them) |
| `buildings` | OSM footprints: `kind`, `poly` (corners in 1/16 tile), `cells` (the tiles they block, delta-coded), `lev` (storeys), `name` only on public landmarks |
| `roads` | one entry per road name and class, with the tiles it covers (delta-coded); the page says "On Tughlak Road" from these |
| `courts` | outlines of the tennis and other courts (`leisure=pitch`), the first number is 0 for tennis, 1 for the rest |
| `trees`, `bushes` | tiles with a tree or a bush |
| `roundabouts`, `signs` | island centres (for the fountains), exit signs where the main roads leave the map |
| `pois` | for each place id of the page: `rect`, `spot`, `entrance` (and `loop`, `steps`) in tiles |
| `walk_metres` | the walking distances behind `world/data/places.json` |

Terrain classes: grass, road, foot, path, water, lawn, wall, gate, tree, flower, rgrass (roundabout island), pgrass
(public park), hedge, sand, bld, court, redwall, parking, plaza. Roads come from `highway=*` ways (the centre line, one
tile wide, widened by the carriageways), footways and steps from `highway=footway|path|steps`, water from
`natural=water`, parks from `leisure=park|garden` and `landuse=grass`, walls from `barrier=wall`, buildings from
`building=*`, courts from `leisure=pitch`, parking from `amenity=parking`.

## Where the map is not OSM

- **Hegel's bungalow is fictional.** It is placed on one real, nameless bungalow footprint on Tughlak Road, inside an inferred
  compound with its gate on the road. No real residence or occupant is named anywhere in the file: buildings carry no
  name except the public landmarks (the four tombs in Lodhi Gardens, Safdarjung's Tomb, Gandhi Smriti, the Gymkhana
  club house, Khan Market, the IIC).
- **Compound walls are mostly inferred.** OSM has the bungalows but hardly any plot boundaries. Around each cluster of
  bungalow buildings the tool draws the plot nearest to it (a Voronoi partition, at most four tiles out), a wall, a gate
  towards the road and a gravel drive. Where OSM maps a wall (`barrier=wall`), that wall is used as mapped. Inferred walls
  are an illustration of the Lutyens plots, not survey data.
- **Trees are invented.** OSM has twenty tree nodes here. Mapped trees and tree rows are used; the avenues, the park
  woodland and the gardens are planted deterministically by the tool.
- Private driveways inside compounds are left out; a few road names use the page's spelling (Tughlaq → Tughlak) or the
  official one (Tees January Marg, Subramania Bharti Marg).
- Walking times: shortest path on the grid between the places' entrances (roads, paths and open ground; not buildings,
  walls, water or trees; diagonals allowed, no corner cutting; grass costs 1.6 and lawns 3 times a road), in metres, at
  75 m a minute. The Directorate of Estates is off the map: the path to the point on the north edge on the way to
  Nirman Bhawan, plus the rest as the crow flies times 1.3.

## Regenerating

```sh
python3 tools/osm_map.py              # reads tools/.cache; fetches only what is missing, 1 request a second
python3 tools/osm_map.py --offline    # never touches the network
python3 tools/osm_map.py --png map.png --no-write   # a debug picture, nothing written
```

The tool uses the OSM API (`api.openstreetmap.org/api/0.6/map`, 40 tiles of 0.004 degrees), not the Overpass API. The
raw XML is cached under `tools/.cache/` (not committed); delete it to fetch the extract afresh. This is a one-off
extract: the page never calls OpenStreetMap, and neither does the Pi. The tool writes `lutyens.json` and the `"walk"`
block of `world/data/places.json` (nothing else in that file), and prints the walking times before and after.

`python3 -m unittest discover -s tests` checks the projection, the rasterisation, the road names and the walk table on a
small fixture, and that the committed map and the committed walk table agree.
