import torch
import torch.nn as nn
from torchvision import models, transforms
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import io
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Serve static files (for /index.html)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# --- Label mappings (generated from your CSV) ---
family_map = {
    0: 'Boidae',
    1: 'Colubridae',
    2: 'Elapidae',
    3: 'Lamprophiidae',
    4: 'Pythonidae',
    5: 'Viperidae'
}
subfamily_map = {
    0: 'Agkistrodon contortrix',
    1: 'Agkistrodon piscivorus',
    2: 'Ahaetulla nasuta',
    3: 'Ahaetulla prasina',
    4: 'Arizona elegans',
    5: 'Aspidelaps lubricus',
    6: 'Atropoides nummifer',
    7: 'Atractaspis bibronii',
    8: 'Atractaspis microlepidota',
    9: 'Basiliscus basiliscus',
    10: 'Bitis arietans',
    11: 'Bitis gabonica',
    12: 'Bitis nasicornis',
    13: 'Bitis peringueyi',
    14: 'Bitis rhinoceros',
    15: 'Boiga dendrophila',
    16: 'Boiga irregularis',
    17: 'Boiga nigriceps',
    18: 'Boiga siamensis',
    19: 'Bothrops alternatus',
    20: 'Bothrops asper',
    21: 'Bothrops atrox',
    22: 'Bothrops jararaca',
    23: 'Bothrops jararacussu',
    24: 'Bothrops moojeni',
    25: 'Bungarus candidus',
    26: 'Bungarus caeruleus',
    27: 'Bungarus fasciatus',
    28: 'Bungarus multicinctus',
    29: 'Calliophis bivirgatus',
    30: 'Calliophis intestinalis',
    31: 'Calloselasma rhodostoma',
    32: 'Candoia aspera',
    33: 'Cerastes cerastes',
    34: 'Cerastes vipera',
    35: 'Chrysopelea ornata',
    36: 'Crotalus adamanteus',
    37: 'Crotalus atrox',
    38: 'Crotalus cerastes',
    39: 'Crotalus horridus',
    40: 'Crotalus molossus',
    41: 'Crotalus oreganus',
    42: 'Crotalus ruber',
    43: 'Crotalus scutulatus',
    44: 'Crotalus simus',
    45: 'Crotalus tigris',
    46: 'Crotalus viridis',
    47: 'Daboia russelii',
    48: 'Dasypeltis scabra',
    49: 'Dendrelaphis pictus',
    50: 'Dendroaspis angusticeps',
    51: 'Dendroaspis jamesoni',
    52: 'Dendroaspis polylepis',
    53: 'Dendroaspis viridis',
    54: 'Dispholidus typus',
    55: 'Drymarchon corais',
    56: 'Drymobius margaritiferus',
    57: 'Drymoluber dichrous',
    58: 'Echis carinatus',
    59: 'Echis coloratus',
    60: 'Echis ocellatus',
    61: 'Echis pyramidum',
    62: 'Elaphe guttata',
    63: 'Elaphe obsoleta',
    64: 'Elaphe quatuorlineata',
    65: 'Elaphe radiata',
    66: 'Elaphe schrenckii',
    67: 'Emydocephalus annulatus',
    68: 'Enhydris enhydris',
    69: 'Eryx johnii',
    70: 'Eryx tataricus',
    71: 'Eunectes murinus',
    72: 'Gonyosoma oxycephalum',
    73: 'Gyalopion quadrangulare',
    74: 'Hemachatus haemachatus',
    75: 'Heterodon nasicus',
    76: 'Hydrophis belcheri',
    77: 'Hydrophis cyanocinctus',
    78: 'Hydrophis platurus',
    79: 'Hydrophis schistosus',
    80: 'Hydrodynastes gigas',
    81: 'Indotyphlops braminus',
    82: 'Lampropeltis californiae',
    83: 'Lampropeltis triangulum',
    84: 'Liasis mackloti',
    85: 'Liasis olivaceus',
    86: 'Lycodon aulicus',
    87: 'Lycodon capucinus',
    88: 'Lytorhynchus diadema',
    89: 'Macrelaps microlepidotus',
    90: 'Malpolon monspessulanus',
    91: 'Masticophis flagellum',
    92: 'Micrurus fulvius',
    93: 'Micrurus lemniscatus',
    94: 'Micrurus nigrocinctus',
    95: 'Micrurus spixii',
    96: 'Micrurus surinamensis',
    97: 'Micrurus tener',
    98: 'Naja annulata',
    99: 'Naja atra',
    100: 'Naja haje',
    101: 'Naja kaouthia',
    102: 'Naja melanoleuca',
    103: 'Naja mossambica',
    104: 'Naja naja',
    105: 'Naja nigricollis',
    106: 'Naja nivea',
    107: 'Naja oxiana',
    108: 'Naja pallida',
    109: 'Naja philippinensis',
    110: 'Naja samarensis',
    111: 'Naja siamensis',
    112: 'Naja sputatrix',
    113: 'Naja sumatrana',
    114: 'Naja atra–specific antivenom',
    115: 'Natrix natrix',
    116: 'Ophiophagus hannah',
    117: 'Oxybelis aeneus',
    118: 'Pantherophis guttatus',
    119: 'Pantherophis obsoletus',
    120: 'Pantherophis spiloides',
    121: 'Pelamis platura',
    122: 'Philodryas baroni',
    123: 'Philodryas olfersii',
    124: 'Philodryas patagoniensis',
    125: 'Phrynonax poecilonotus',
    126: 'Pituophis catenifer',
    127: 'Porthidium nasutum',
    128: 'Pseudechis australis',
    129: 'Pseudechis colleti',
    130: 'Pseudechis guttatus',
    131: 'Pseudechis porphyriacus',
    132: 'Pseudechis weigeli',
    133: 'Pseudonaja affinis',
    134: 'Pseudonaja nuchalis',
    135: 'Pseudonaja textilis',
    136: 'Psammophis schokari',
    137: 'Python bivittatus',
    138: 'Python curtus',
    139: 'Python molurus',
    140: 'Python regius',
    141: 'Python sebae',
    142: 'Rhabdophis tigrinus',
    143: 'Rhinocheilus lecontei',
    144: 'Sistrurus catenatus',
    145: 'Sistrurus miliarius',
    146: 'Spilotes pullatus',
    147: 'Telescopus fallax',
    148: 'Telescopus semiannulatus',
    149: 'Thamnophis elegans',
    150: 'Thamnophis radix',
    151: 'Thamnophis sirtalis',
    152: 'Trimorphodon biscutatus',
    153: 'Tropidolaemus wagleri',
    154: 'Vipera ammodytes',
    155: 'Vipera aspis',
    156: 'Vipera berus',
    157: 'Vipera latastei',
    158: 'Vipera ursinii',
    159: 'Xenochrophis piscator',
    160: 'Xenopeltis unicolor',
    161: 'Xylophis mosaicus',
    162: 'Zamenis longissimus',
    163: 'Zamenis scalaris',
    164: 'Zamenis situla'
}
antidote_map = {
    0: '\tAntivipmyn TRI® / local polyvalent', 1: 'Antivipmyn TRI®',
    2: 'Black Snake Antivenom', 3: 'Boomslang-specific monovalent antivenom',
    4: 'Bothrops antivenom', 5: 'Brown Snake Antivenom', 6: 'Coral Snake Antivenin',
    7: 'CroFab', 8: 'CroFab®', 9: 'CroFab® / ANAVIP', 10: 'European viper antivenoms',
    11: 'Green Pit Viper / Regional Viper Antivenom', 12: 'Green Pit Viper Antivenom',
    13: 'Indian Polyvalent Antivenom', 14: 'Inoserp Europe / ViperaTAb',
    15: 'King Cobra Monovalent Antivenom', 16: 'Monovalent or polyvalent cobra antivenom',
    17: 'N.A', 18: 'N.A.', 19: 'Naja atra\x96specific antivenom',
    20: 'No Anti-Venom Required', 21: 'Polyvalent pit viper antivenom',
    22: 'SAIMR / INOSAN / African polyvalent', 23: 'SAIMR Black Mamba Antivenom / Polyvalent',
    24: 'SAIMR Polyvalent Antivenom', 25: 'Taipan Antivenom',
    26: 'Taiwan CDC Monovalent or Polyvalent Viper Antivenom',
    27: 'Tiger Snake Antivenom', 28: 'Tiger Snake Antivenom (Seqirus)',
    29: 'elapid polyvalent', 30: 'polyvalent elapid antivenom'
}
# --- Optionally, merge antidote classes as you requested ---
def merge_antidote_label(antidote_text):
    if antidote_text.strip() in ['N.A', 'N.A.', 'No Anti-Venom Required']:
        return 'No Antidote Required'
    return antidote_text.strip()

# --- Model definition (from your notebook) ---
class SnakeClassifier(nn.Module):
    def __init__(self, num_families=6, num_subfamilies=165, num_antidotes=31):
        super(SnakeClassifier, self).__init__()
        self.backbone = models.resnet18(pretrained=False)
        num_feats = models.resnet18().fc.in_features
        self.backbone = nn.Sequential(*list(self.backbone.children())[:-1])
        self.family_head = nn.Linear(num_feats, num_families)
        self.subfamily_head = nn.Linear(num_feats, num_subfamilies)
        self.antidote_head = nn.Linear(num_feats, num_antidotes)

    def forward(self, x):
        x = self.backbone(x)
        x = torch.flatten(x, 1)
        out_family = self.family_head(x)
        out_subfamily = self.subfamily_head(x)
        out_antidote = self.antidote_head(x)
        return out_family, out_subfamily, out_antidote

# --- FastAPI App ---
app = FastAPI()

# --- Image Preprocessing (exact from training) ---
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# --- Load Model ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SnakeClassifier()
model.load_state_dict(torch.load("model_best_augmented.pt", map_location=device))
model.eval()
model.to(device)

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        # Read and preprocess image
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        input_tensor = preprocess(image).unsqueeze(0).to(device)
        
        # Inference
        with torch.no_grad():
            out_family, out_subfamily, out_antidote = model(input_tensor)
            family_idx = out_family.argmax(dim=1).item()
            subfamily_idx = out_subfamily.argmax(dim=1).item()
            antidote_idx = out_antidote.argmax(dim=1).item()

        # Map predictions to labels (with antidote merging)
        family_label = family_map.get(family_idx, "Unknown")
        subfamily_label = subfamily_map.get(subfamily_idx, "Unknown")
        antidote_label_raw = antidote_map.get(antidote_idx, "Unknown")
        antidote_label = merge_antidote_label(antidote_label_raw)
        
        result = {
            "family": family_label,
            "sub_family": subfamily_label,
            "antidote": antidote_label
        }
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/")
def read_index():
    return FileResponse('index.html')

# @app.get("/index.html")
# def read_index_html():
#     return FileResponse('index.html')
