import os
from ax.service.ax_client import AxClient
import ax
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from matplotlib.patches import Rectangle
import numpy as np
import matplotlib.pyplot as plt
from rdkit.Chem import Draw
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


exp_dict = {
    'IBP': {'experiment_folder': '2026-02-19','iteration': 10,},
    'LOV': {'experiment_folder': '2026-02-20','iteration': 10,},
    'DCF': {'experiment_folder': '2026-02-23','iteration': 10,},
    'GLV': {'experiment_folder': '2026-02-26','iteration': 10,}
}


drug_dict = {
    "IBP": {"full_name": "Ibuprofen", "abbr": "IBP", "CAS": "15687-27-1", "smiles": "O=C(O)C(C1=CC=C(C=C1)CC(C)C)C"},
    "DCF": {"full_name": "Diclofenac", "abbr": "DCF", "CAS": "15307-86-5", "smiles": "O=C(O)CC=1C=CC=CC1NC=2C(Cl)=CC=CC2Cl"},
    "LOV": {"full_name": "Lovastatin", "abbr": "LOV", "CAS": "75330-75-5", "smiles": "O=C1OC(CCC2C(C=CC3=CC(C)CC(OC(=O)C(C)CC)C32)C)CC(O)C1"}, 
    "GLV": {"full_name": "Griseofulvin", "abbr": "GLV", "CAS": "126-07-8", "smiles": "O=C1C=C(OC)C2(OC=3C(Cl)=C(OC)C=C(OC)C3C2=O)C(C)C1"}, 
}


surfactant_dict = {
    's1':{"abbr": "SDS", "full_name": "Sodium Dodecyl Sulfate"},
    's2':{"abbr": "NaC", "full_name": "Sodium Cholate"},
    's3':{"abbr": "CHAPS", "full_name": "3-[(3-Cholamidopropyl)dimethylammonio]-1-propanesulfonate"},
    's4':{"abbr": "DTAB", "full_name": "Dodecyltrimethylammonium Bromide"},
    's5':{"abbr": "TTAB", "full_name": "Tetradecyltrimethylammonium Bromide"},
    's6':{"abbr": "P188", "full_name": "Poloxamer 188"},
    's7':{"abbr": "P407", "full_name": "Poloxamer 407"},
    's8':{"abbr": "SB3-12", "full_name": "Lauryl Sulfobetaine"},
}

# converting factor: 1200 total surfactants vs 270 trials
factor = 1 / 1200 * 270

def add_iteration_number(df, trials_per_iteration, num_random_trials):
    df = df.copy()
    df['iteration'] = 0
    mask = df['trial_index'] >= num_random_trials
    df.loc[mask, 'iteration'] = ((df.loc[mask, 'trial_index'] - num_random_trials) // trials_per_iteration) + 1
    return df

def add_success_column(df, threshold):
    df = df.copy()
    df['success'] = (df['absorbance'] < threshold).astype(int)
    return df

# replace the column names s1 to s8 to surfactant names
def replace_surfacant_names(df):
    df = df.copy()
    df = df.rename(columns={key: surfactant_dict[key]['abbr'] for key in surfactant_dict.keys()})
    return df


def data_summary():
    for drug in exp_dict.keys():

        experiment_folder = exp_dict[drug]['experiment_folder']
        iteration = exp_dict[drug]['iteration']

        optimizer_path = f'../{experiment_folder}/optimizer/optimizer_{iteration}_loaded.json'
        params_path = f'../{experiment_folder}/experiment_parameters.csv'


        exp_params = pd.read_csv(params_path)
        exp_params_dict = dict(zip(exp_params.iloc[:, 0], exp_params.iloc[:, 1]))

        exp_dict[drug]['exp_params'] = exp_params_dict

        ax_client = AxClient.load_from_json_file(optimizer_path)
        df = ax_client.get_trials_data_frame()

        for col in surfactant_dict.keys():
            df[col] = df[col] * factor

        df = add_iteration_number(df, int(exp_params_dict['TRIALS_PER_ITERATION']), int(exp_params_dict['NUM_RANDOM_TRIALS']))
        df = add_success_column(df, float(exp_params_dict['ABSORBANCE_THRESHOLD']))
        df = replace_surfacant_names(df)
        df['obj_total_vol'] = df['obj_total_vol'] * factor  # add this line

        


        exp_dict[drug]['results'] = df

        exp_dict[drug]['ax_client'] = ax_client

    return exp_dict



def drug_visualization(drug_dict):

    prop_keys   = ['mol_weight', 'log_p', 'hbd', 'hba', 'tpsa', 'rot_bonds']
    axes_labels = [
        'MW (Da)',
        'Log P',
        'H-Bond\nDonors',
        'H-Bond\nAcceptors',
        'Polar Surface\nArea (Å²)',
        'Rotatable\nBonds',
    ]

    # ── Compute properties from SMILES ────────────────────────────────
    abbrs = list(drug_dict.keys())
    data  = {}
    for abbr, info in drug_dict.items():
        mol = Chem.MolFromSmiles(info['smiles'])
        data[abbr] = {
            'full_name':  info['full_name'],
            'mol_weight': round(Descriptors.MolWt(mol), 1),
            'log_p':      round(Descriptors.MolLogP(mol), 1),
            'hbd':        rdMolDescriptors.CalcNumHBD(mol),
            'hba':        rdMolDescriptors.CalcNumHBA(mol),
            'tpsa':       round(rdMolDescriptors.CalcTPSA(mol), 1),
            'rot_bonds':  rdMolDescriptors.CalcNumRotatableBonds(mol),
        }

    # Office 2019 accent palette: blue / green / red / purple
    colors = ['#4472C4', '#70AD47', '#C00000', '#7030A0']
    colors = ['#4878CF', '#6ACC65', '#F36D6D', '#B47CC7']
    n_axes = len(prop_keys)
    xs     = np.arange(n_axes, dtype=float)

    # ── Per-axis normalisation: 20% padding beyond actual min/max ─────
    def norm(key, val):
        lo  = min(data[a][key] for a in abbrs)
        hi  = max(data[a][key] for a in abbrs)
        rng = hi - lo if hi != lo else 1.0
        return (val - (lo - 0.20 * rng)) / (1.40 * rng)

    # ── Per-segment sigmoid (cubic Hermite, zero endpoint tangents) ───
    # y(t) = y0*(1-t)^2*(1+2t) + y1*t^2*(3-2t)   t in [0,1]
    def sigmoid_segment(x0, y0, x1, y1, n=150):
        t  = np.linspace(0, 1, n)
        xf = x0 + t * (x1 - x0)
        yf = y0 * (1 - t)**2 * (1 + 2*t) + y1 * t**2 * (3 - 2*t)
        return xf, yf

    # ── Figure ────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(15, 5.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.set_xlim(-0.55, n_axes - 0.45)
    ax.set_ylim(-0.20, 1.2)
    ax.axis('off')

    # ── Background bands: segmented per column, with gaps at each axis ─
    # Gap on each side of every axis line so bands appear "divided"
    BGGAP = 0.04
    band_colors = ['#ECEFF8', '#F7F9FC']
    # Column x-boundaries: left edge, between axes, right edge
    col_edges = (
        [xs[0] - 0.5] +
        [x + BGGAP for x in xs[:-1]] +
        [xs[-1] + 0.5]
    )
    # Each inter-axis column spans col_edges[i] .. col_edges[i+1],
    # but split at internal axis gaps: left half and right half
    # Simpler: just draw one rect per gap-delimited segment
    seg_bounds = []
    seg_bounds.append((xs[0] - 0.5, xs[0] - BGGAP))   # leftmost stub
    for i in range(n_axes - 1):
        seg_bounds.append((xs[i] + BGGAP, xs[i+1] - BGGAP))
    seg_bounds.append((xs[-1] + BGGAP, xs[-1] + 0.5))  # rightmost stub

    for i in range(4):
        y0_band = i * 0.25
        for x_left, x_right in seg_bounds:
            rect = Rectangle(
                (x_left, y0_band), x_right - x_left, 0.25,
                facecolor=band_colors[i % 2], alpha=1.0,
                linewidth=0, zorder=0, transform=ax.transData
            )
            ax.add_patch(rect)

    # ── Pre-compute normalised y ──────────────────────────────────────
    all_yn = {a: np.array([norm(k, data[a][k]) for k in prop_keys]) for a in abbrs}

    # ── Vertical axis lines with white gaps where curves cross ────────
    AXGAP = 0.045
    for axis_i, xi in enumerate(xs):
        crossings = sorted(all_yn[a][axis_i] for a in abbrs)
        breaks = []
        for yc in crossings:
            lo_b, hi_b = yc - AXGAP, yc + AXGAP
            if breaks and lo_b < breaks[-1][1]:
                breaks[-1] = (breaks[-1][0], max(hi_b, breaks[-1][1]))
            else:
                breaks.append((lo_b, hi_b))
        segments = []
        prev = 0.0
        for lo_b, hi_b in breaks:
            if prev < lo_b:
                segments.append((prev, lo_b))
            prev = hi_b
        if prev < 1.0:
            segments.append((prev, 1.0))
        for y0_seg, y1_seg in segments:
            ax.plot([xi, xi], [y0_seg, y1_seg], color='#B8BED0', lw=1.1,
                    zorder=2, solid_capstyle='butt')

    # ── Draw continuous per-segment sigmoid curves ────────────────────
    for abbr, color in zip(abbrs, colors):
        yn = all_yn[abbr]

        for seg in range(n_axes - 1):
            xf, yf = sigmoid_segment(xs[seg], yn[seg], xs[seg+1], yn[seg+1])
            # Two-layer glow
            ax.fill_between(xf, yf - 0.040, yf + 0.040,
                            color=color, alpha=0.09, linewidth=0, zorder=3)
            ax.fill_between(xf, yf - 0.016, yf + 0.016,
                            color=color, alpha=0.13, linewidth=0, zorder=3)
            # Main solid curve (continuous)
            ax.plot(xf, yf, color=color, lw=2.4, alpha=0.93, zorder=4,
                    solid_capstyle='round', solid_joinstyle='round')

        # White-bordered circle markers at each axis
        for xi, y in zip(xs, yn):
            ax.scatter(xi, y, s=80, color=color, zorder=6,
                       edgecolors='white', linewidths=1.4)

    # ── Value labels: bottom-up to prevent upward stacking drift ─────
    for axis_i, key in enumerate(prop_keys):
        xi = float(axis_i)
        entries = sorted(
            [(all_yn[a][axis_i], data[a][key], colors[j])
             for j, a in enumerate(abbrs)],
            key=lambda t: t[0]
        )
        placed_y = []
        for y_norm, raw_val, color in entries:
            y_text = y_norm + 0.025
            if placed_y and y_text < placed_y[-1] + 0.060:
                y_text = placed_y[-1] + 0.060
            placed_y.append(y_text)
            ax.text(xi + 0.07, y_text, str(raw_val),
                    fontsize=12.5, color=color, ha='left', va='bottom',
                     zorder=7)

    # ── Column headers ────────────────────────────────────────────────
    for xi, label in zip(xs, axes_labels):
        ax.text(xi, 1.10, label, ha='center', va='bottom',
                fontsize=12.5, color="#000000",
                multialignment='center', zorder=8)

    # ── Legend ────────────────────────────────────────────────────────
    legend_handles = [
        plt.Line2D([0], [0], color=colors[i], lw=1.8, linestyle='--',
                   marker='o', markersize=7,
                   markerfacecolor=colors[i], markeredgecolor='white',
                   markeredgewidth=1.0,
                   label=f'{data[abbrs[i]]["full_name"]} ({abbrs[i]})')
        for i in range(len(abbrs))
    ]
    ax.legend(handles=legend_handles, loc='lower center',
              bbox_to_anchor=(0.5, 0.0), ncol=len(abbrs),
              fontsize=12.5, frameon=False,
              handlelength=2.5, handletextpad=0.6, columnspacing=2.0)

    fig.tight_layout()
    plt.show()

    save_path = f'figures/drug_properties.png'
    fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())




# ── Publication export ────────────────────────────────────────────────────────
# Journal revision: double-column figures 17.8 cm wide, single-column 8.5 cm,
# vector output, 300 ppi, transparent background.
CM            = 1 / 2.54          # inches per cm
DOUBLE_COL_CM = 17.8
SINGLE_COL_CM = 8.5
EXPORT_DPI    = 300

plt.rcParams.update({
    'pdf.fonttype': 42,       # embed TrueType -> text stays editable in Illustrator
    'ps.fonttype':  42,
    'svg.fonttype': 'none',   # keep text as text in SVG
})


def save_publication_figure(fig, stem, width_cm):
    """Save `fig` as vector PDF + SVG and a 300-ppi PNG, transparent background.

    bbox_inches='tight' is deliberately NOT used: it would crop the page and
    change the width, whereas the journal requires an exact width.
    """
    w_in = fig.get_size_inches()[0]
    if abs(w_in - width_cm * CM) > 1e-3:
        raise ValueError(f'Figure is {w_in / CM:.2f} cm wide, expected {width_cm} cm')
    os.makedirs('figures', exist_ok=True)
    paths = []
    for ext in ('pdf', 'svg', 'png'):
        path = f'figures/{stem}.{ext}'
        fig.savefig(path, dpi=EXPORT_DPI, transparent=True)
        paths.append(path)
    print('Saved → ' + ', '.join(paths))


# ── Vector 2D structure drawing (replaces the raster Draw.MolToImage) ─────────
_ATOM_COLORS = {'O': '#E00000', 'N': '#1F3FD0', 'S': '#B8A000',
                'F': '#1E9E1E', 'Cl': '#1E9E1E', 'Br': '#A0291E'}


def _mol_coords(mol):
    """2D depiction coordinates scaled to a bond length of 1."""
    from rdkit.Chem import rdDepictor
    mol = Chem.Mol(mol)
    rdDepictor.SetPreferCoordGen(True)
    rdDepictor.Compute2DCoords(mol)
    conf = mol.GetConformer()
    xy = np.array([[conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y]
                   for i in range(mol.GetNumAtoms())])
    bl = np.mean([np.linalg.norm(xy[b.GetBeginAtomIdx()] - xy[b.GetEndAtomIdx()])
                  for b in mol.GetBonds()])
    xy = (xy - xy.mean(axis=0)) / bl
    return mol, xy


def _draw_molecule(ax, mol, xy, pts_per_unit, fontsize=6.0, lw=0.7,
                   bond_color='#222222'):
    """Draw a skeletal formula with matplotlib lines/text (fully vector)."""
    ring_info  = mol.GetRingInfo()
    arom_rings = [set(r) for r in ring_info.AtomRings()
                  if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in r)]
    kek = Chem.Mol(mol)
    Chem.Kekulize(kek, clearAromaticFlags=True)

    labelled = {a.GetIdx() for a in kek.GetAtoms() if a.GetSymbol() != 'C'}
    trim = 0.62 * fontsize / pts_per_unit       # gap around atom labels

    def seg(p, q, i, j, shrink_i=0.0, shrink_j=0.0):
        u = (q - p) / np.linalg.norm(q - p)
        a = p + u * max(shrink_i, trim if i in labelled else 0.0)
        b = q - u * max(shrink_j, trim if j in labelled else 0.0)
        ax.plot([a[0], b[0]], [a[1], b[1]], color=bond_color, lw=lw,
                solid_capstyle='round', zorder=2)

    for bond in kek.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        p, q = xy[i], xy[j]
        order = bond.GetBondTypeAsDouble()
        u = (q - p) / np.linalg.norm(q - p)
        n = np.array([-u[1], u[0]])
        if order == 2 and ring_info.NumBondRings(bond.GetIdx()):
            # main line + shorter inner line on the ring-centre side
            rings = [r for r in ring_info.AtomRings() if i in r and j in r]
            rings.sort(key=lambda r: (set(r) not in arom_rings, abs(len(r) - 6)))
            centre = xy[list(rings[0])].mean(axis=0)
            if np.dot(centre - (p + q) / 2, n) < 0:
                n = -n
            seg(p, q, i, j)
            seg(p + 0.18 * n, q + 0.18 * n, i, j, 0.17, 0.17)
        elif order == 2:
            seg(p + 0.09 * n, q + 0.09 * n, i, j)
            seg(p - 0.09 * n, q - 0.09 * n, i, j)
        elif order == 3:
            for k in (-0.14, 0, 0.14):
                seg(p + k * n, q + k * n, i, j)
        else:
            seg(p, q, i, j)

    for atom in kek.GetAtoms():
        idx = atom.GetIdx()
        if idx not in labelled:
            continue
        sym   = atom.GetSymbol()
        color = _ATOM_COLORS.get(sym, '#222222')
        x, y  = xy[idx]
        ax.text(x, y, sym, ha='center', va='center', fontsize=fontsize,
                color=color, zorder=3)
        n_h = atom.GetTotalNumHs()
        if n_h:
            nbr_dx = np.mean([xy[nb.GetIdx()][0] - x for nb in atom.GetNeighbors()])
            side   = -1 if nbr_dx > 0 else 1          # put H away from the bonds
            h_txt  = 'H' if n_h == 1 else f'H$_{n_h}$'
            dx     = side * fontsize * (0.42 + 0.28 * len(sym))
            ax.annotate(h_txt, (x, y), xytext=(dx, 0), textcoords='offset points',
                        ha='center', va='center', fontsize=fontsize,
                        color=color, zorder=3)


def drug_visualization(drug_dict, width_cm=DOUBLE_COL_CM, height_cm=10.0):

    prop_keys = ['mol_weight', 'log_p', 'hbd', 'hba', 'tpsa', 'rot_bonds']
    axes_labels = [
        'MW (Da)',
        'Log P',
        'H-Bond\nDonors',
        'H-Bond\nAcceptors',
        'Polar Surface\nArea (Å²)',
        'Rotatable\nBonds',
    ]

    # ── Compute properties from SMILES ───────────────────────────────
    abbrs = list(drug_dict.keys())
    data = {}
    mols = {}

    for abbr, info in drug_dict.items():
        mol = Chem.MolFromSmiles(info['smiles'])
        if mol is None:
            raise ValueError(f"Invalid SMILES for {abbr}")

        mols[abbr] = mol
        data[abbr] = {
            'full_name': info['full_name'],
            'mol_weight': round(Descriptors.MolWt(mol), 1),
            'log_p': round(Descriptors.MolLogP(mol), 1),
            'hbd': rdMolDescriptors.CalcNumHBD(mol),
            'hba': rdMolDescriptors.CalcNumHBA(mol),
            'tpsa': round(rdMolDescriptors.CalcTPSA(mol), 1),
            'rot_bonds': rdMolDescriptors.CalcNumRotatableBonds(mol),
        }

    # ── Sizes (in points, for the printed 17.8 cm figure) ────────────
    FS      = 7.0     # all text
    FS_NAME = 7.5     # coloured drug names under the structures
    LW      = 1.3     # curves
    MS      = 22      # scatter marker area (pt²)

    # ── Colors ───────────────────────────────────────────────────────
    colors = ['#4878CF', '#6ACC65', '#F36D6D', '#B47CC7']
    n_axes = len(prop_keys)
    xs = np.arange(n_axes, dtype=float)

    # ── Per-axis normalisation ───────────────────────────────────────
    def norm(key, val):
        lo = min(data[a][key] for a in abbrs)
        hi = max(data[a][key] for a in abbrs)
        rng = hi - lo if hi != lo else 1.0
        return (val - (lo - 0.20 * rng)) / (1.40 * rng)

    # ── Per-segment sigmoid ──────────────────────────────────────────
    def sigmoid_segment(x0, y0, x1, y1, n=150):
        t = np.linspace(0, 1, n)
        xf = x0 + t * (x1 - x0)
        yf = y0 * (1 - t)**2 * (1 + 2*t) + y1 * t**2 * (3 - 2*t)
        return xf, yf

    # ── Figure ───────────────────────────────────────────────────────
    fig = plt.figure(figsize=(width_cm * CM, height_cm * CM))
    ax = fig.add_axes([0.01, 0.0, 0.98, 0.62])
    ax.set_xlim(-0.55, n_axes - 0.45)
    ax.set_ylim(-0.24, 1.2)
    ax.axis('off')

    # ── Background bands ─────────────────────────────────────────────
    BGGAP = 0.04
    band_colors = ['#ECEFF8', '#F7F9FC']

    seg_bounds = [(xs[0] - 0.5, xs[0] - BGGAP)]
    for i in range(n_axes - 1):
        seg_bounds.append((xs[i] + BGGAP, xs[i+1] - BGGAP))
    seg_bounds.append((xs[-1] + BGGAP, xs[-1] + 0.5))

    for i in range(4):
        y0_band = i * 0.25
        for x_left, x_right in seg_bounds:
            ax.add_patch(Rectangle(
                (x_left, y0_band), x_right - x_left, 0.25,
                facecolor=band_colors[i % 2], linewidth=0, zorder=0,
            ))

    # ── Pre-compute normalised y ──────────────────────────────────────
    all_yn = {
        a: np.array([norm(k, data[a][k]) for k in prop_keys])
        for a in abbrs
    }

    # ── Vertical axis lines (with gaps where curves cross) ───────────
    AXGAP = 0.045

    for axis_i, xi in enumerate(xs):
        crossings = sorted(all_yn[a][axis_i] for a in abbrs)
        breaks = []
        for yc in crossings:
            lo_b, hi_b = yc - AXGAP, yc + AXGAP
            if breaks and lo_b < breaks[-1][1]:
                breaks[-1] = (breaks[-1][0], max(hi_b, breaks[-1][1]))
            else:
                breaks.append((lo_b, hi_b))

        segments = []
        prev = 0.0
        for lo_b, hi_b in breaks:
            if prev < lo_b:
                segments.append((prev, lo_b))
            prev = hi_b
        if prev < 1.0:
            segments.append((prev, 1.0))

        for y0_seg, y1_seg in segments:
            ax.plot([xi, xi], [y0_seg, y1_seg], color='#B8BED0', lw=0.6,
                    zorder=2, solid_capstyle='butt')

    # ── Draw continuous sigmoid curves ───────────────────────────────
    for abbr, color in zip(abbrs, colors):
        yn = all_yn[abbr]
        for seg in range(n_axes - 1):
            xf, yf = sigmoid_segment(xs[seg], yn[seg], xs[seg+1], yn[seg+1])
            ax.fill_between(xf, yf - 0.040, yf + 0.040, color=color,
                            alpha=0.09, linewidth=0, zorder=3)
            ax.fill_between(xf, yf - 0.016, yf + 0.016, color=color,
                            alpha=0.13, linewidth=0, zorder=3)
            ax.plot(xf, yf, color=color, lw=LW, alpha=0.93, zorder=4,
                    solid_capstyle='round', solid_joinstyle='round')

        ax.scatter(xs, yn, s=MS, color=color, zorder=6,
                   edgecolors='white', linewidths=0.6)

    # ── Value labels (pushed upward when they would overlap) ─────────
    min_gap = 1.3 * FS / (ax.get_position().height * fig.get_figheight() * 72 / 1.44)
    for axis_i, key in enumerate(prop_keys):
        entries = sorted(
            [(all_yn[a][axis_i], data[a][key], colors[j]) for j, a in enumerate(abbrs)],
            key=lambda t: t[0],
        )
        placed_y = []
        for y_norm, raw_val, color in entries:
            y_text = y_norm + 0.025
            if placed_y and y_text < placed_y[-1] + min_gap:
                y_text = placed_y[-1] + min_gap
            placed_y.append(y_text)
            ax.text(axis_i + 0.06, y_text, str(raw_val), fontsize=FS,
                    color=color, ha='left', va='bottom', zorder=7)

    # ── Column headers ───────────────────────────────────────────────
    for xi, label in zip(xs, axes_labels):
        ax.text(xi, 1.08, label, ha='center', va='bottom', fontsize=FS,
                color='#000000', multialignment='center', zorder=8)

    # ── Molecular structures (vector), one common bond length ────────
    n_drugs   = len(abbrs)
    row_left, row_width = 0.04, 0.92
    slot_w    = row_width / n_drugs
    mol_box   = [0.705, 0.285]               # [bottom, height] in fig fraction
    coords    = {a: _mol_coords(mols[a]) for a in abbrs}
    half_w    = max(np.ptp(xy[:, 0]) for _, xy in coords.values()) / 2 + 0.6
    half_h    = max(np.ptp(xy[:, 1]) for _, xy in coords.values()) / 2 + 0.6
    box_w_pt  = (slot_w - 0.01) * fig.get_figwidth() * 72
    box_h_pt  = mol_box[1] * fig.get_figheight() * 72
    pts_per_unit = min(box_w_pt / (2 * half_w), box_h_pt / (2 * half_h))

    for i, (abbr, color) in enumerate(zip(abbrs, colors)):
        x_left = row_left + i * slot_w
        ax_mol = fig.add_axes([x_left + 0.005, mol_box[0], slot_w - 0.01, mol_box[1]])
        ax_mol.axis('off')
        mol_k, xy = coords[abbr]
        hw = box_w_pt / pts_per_unit / 2
        hh = box_h_pt / pts_per_unit / 2
        ax_mol.set_xlim(-hw, hw)
        ax_mol.set_ylim(-hh, hh)
        _draw_molecule(ax_mol, mol_k, xy, pts_per_unit, fontsize=5.5, lw=0.6)

        fig.text(x_left + slot_w / 2, 0.695, f'{data[abbr]["full_name"]} ({abbr})',
                 ha='center', va='top', fontsize=FS_NAME, fontweight='bold',
                 color=color)

    # ── Legend ───────────────────────────────────────────────────────
    legend_handles = [
        plt.Line2D([0], [0], color=colors[i], lw=1.0, linestyle='--',
                   marker='o', markersize=4, markerfacecolor=colors[i],
                   markeredgecolor='white', markeredgewidth=0.6,
                   label=f'{data[abbrs[i]]["full_name"]} ({abbrs[i]})')
        for i in range(len(abbrs))
    ]
    ax.legend(handles=legend_handles, loc='lower center',
              bbox_to_anchor=(0.5, 0.0), ncol=len(abbrs), fontsize=FS,
              frameon=False, handlelength=2.5, handletextpad=0.5,
              columnspacing=2.0)

    # ── Save and display ─────────────────────────────────────────────
    save_publication_figure(fig, 'drug_properties', width_cm)
    plt.show()



def plot_surfactant_combined(df, drug, success_only=False, transparent=True,
                             width_cm=DOUBLE_COL_CM, height_cm=13.0):
    """Three-panel optimisation trace. Exported at `width_cm` (17.8 cm) as
    PDF/SVG/300-ppi PNG; `transparent` controls the exported background."""
    from matplotlib.patches import Polygon

    surfactants = [surfactant_dict[key]['abbr'] for key in surfactant_dict.keys()][::-1]

    palette = [
        '#4878CF', '#6ACC65', "#F36D6D", '#B47CC7',
        '#C4AD66', '#77BEDB', '#E68310', "#911828"
    ]

    # Always use full df for best-so-far; success_only only affects stacked bars & bubble
    all_iters   = sorted(df['iteration'].unique())
    data        = df[df['success'] == 1] if success_only else df
    iters       = list(all_iters)
    n_iter      = len(iters)
    grouped     = data.groupby('iteration')[surfactants].mean().reindex(all_iters)

    region_defs = [
        (0, 0,           '#888888', 'Random'),
        (1, 4,           '#3A7DC9', 'Explore'),
        (5, 8,           '#2A9D5C', 'Explore/Exploit'),
        (9, max(iters),  '#C05046', 'Exploit'),
    ]

    # ── Best-so-far computation (always from full df, success==1) ──────
    successful       = df[df['success'] == 1]
    iter_best        = successful.groupby('iteration')['obj_total_vol'].min()
    iter_best_full   = iter_best.reindex(all_iters)
    best_so_far      = iter_best_full.cummin().ffill()

    # ── Sizes (points) for the printed 17.8 cm figure ──────────────────
    FS       = 7.0    # axis labels, legend
    FS_TICK  = 6.5
    FS_SMALL = 6.0    # region labels
    FS_PANEL = 8.0    # a) b) c)
    FS_TITLE = 9.0

    rc = {
        'font.family': 'DejaVu Sans', 'font.size': FS,
        'axes.linewidth': 0.6,
        'axes.spines.top': False, 'axes.spines.right': False,
        'xtick.direction': 'out', 'ytick.direction': 'out',
        'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
        'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
        'xtick.labelsize': FS_TICK, 'ytick.labelsize': FS_TICK,
        'axes.labelsize': FS,
    }

    bar_w = 0.55

    def get_region_x_bounds(lo, hi):
        xs = [x for x in iters if lo <= x <= hi]
        if not xs:
            return None
        return min(xs) - bar_w / 2 - 0.1, max(xs) + bar_w / 2 + 0.1

    def draw_region_shading(ax):
        for lo, hi, color, label in region_defs:
            bounds = get_region_x_bounds(lo, hi)
            if bounds is None:
                continue
            x0, x1 = bounds
            ax.axvspan(x0, x1, color=color, alpha=0.06, zorder=0, linewidth=0)

    def sep_lines(ax):
        for sx in [0.5, 4.5, 8.5]:
            if min(iters) < sx < max(iters):
                ax.axvline(sx, color='#444444', lw=0.6,
                           linestyle='--', dashes=(4, 2.5), zorder=4, alpha=0.5)

    def region_labels(ax, y_bracket, y_text):
        for lo, hi, color, label in region_defs:
            xs = [x for x in iters if lo <= x <= hi]
            if not xs:
                continue
            ax.annotate('', xy=(max(xs) + 0.45, y_bracket),
                        xytext=(min(xs) - 0.45, y_bracket),
                        arrowprops=dict(arrowstyle='-', color=color, lw=0.9))
            ax.text((min(xs) + max(xs)) / 2, y_text, label,
                    ha='center', va='bottom', fontsize=FS_SMALL,
                    color=color, fontweight='semibold')

    with plt.rc_context(rc):
        fig = plt.figure(figsize=(width_cm * CM, height_cm * CM))
        # Fixed margins (no tight_layout / bbox 'tight') -> exact exported width
        gs = fig.add_gridspec(3, 1, left=0.085, right=0.885, bottom=0.075,
                              top=0.915, hspace=0.28)
        ax_best = fig.add_subplot(gs[1, 0])
        ax_top  = fig.add_subplot(gs[0, 0], sharex=ax_best)
        ax_bot  = fig.add_subplot(gs[2, 0], sharex=ax_best)

        x_lo = min(iters) - bar_w
        x_hi = max(iters) + bar_w

        # ══ BEST-SO-FAR ════════════════════════════════════════════════
        draw_region_shading(ax_best)

        valid_bsf = best_so_far.dropna()
        ax_best.step(valid_bsf.index, valid_bsf.values,
                     where='post', color='#C05046', lw=1.2,
                     zorder=5, label='Best so far')
        ax_best.fill_between(valid_bsf.index, valid_bsf.values,
                             valid_bsf.values.max() * 1.00,
                             step='post', color='#C05046', alpha=0.08, zorder=0)

        bsf_min = valid_bsf.min() if len(valid_bsf) else 0
        bsf_max = valid_bsf.max() if len(valid_bsf) else 1
        pad = (bsf_max - bsf_min) * 0.25 if bsf_max > bsf_min else 1
        ax_best.set_ylim(max(0, bsf_min - pad), bsf_max + pad * 1.5)
        ax_best.set_xlim(x_lo, x_hi)
        ax_best.set_ylabel('Best/Lowest\nSurfactant Vol (µL)', labelpad=4)
        ax_best.yaxis.grid(True, color='#e0e0e0', linewidth=0.4, zorder=1)
        ax_best.set_axisbelow(True)
        sep_lines(ax_best)
        plt.setp(ax_best.get_xticklabels(), visible=False)

        # ══ STACKED BARS ═══════════════════════════════════════════════
        cum = np.zeros(n_iter)
        bar_bottoms, bar_tops = [], []
        for s in surfactants:
            bar_bottoms.append(cum.copy())
            cum = cum + grouped[s].values
            bar_tops.append(cum.copy())

        y_max = bar_tops[-1].max()
        draw_region_shading(ax_top)

        for j, s in enumerate(surfactants):
            color = palette[j]
            for i in range(n_iter - 1):
                xl = iters[i]   + bar_w / 2
                xr = iters[i+1] - bar_w / 2
                poly = Polygon(list(zip(
                    [xl, xr, xr, xl],
                    [bar_tops[j][i],      bar_tops[j][i+1],
                     bar_bottoms[j][i+1], bar_bottoms[j][i]]
                )), closed=True, facecolor=color, alpha=0.18, linewidth=0)
                ax_top.add_patch(poly)
                ax_top.plot([xl, xr], [bar_tops[j][i],     bar_tops[j][i+1]],
                            color=color, lw=0.45, alpha=0.55, zorder=2)
                ax_top.plot([xl, xr], [bar_bottoms[j][i],  bar_bottoms[j][i+1]],
                            color=color, lw=0.45, alpha=0.55, zorder=2)

        for j, s in enumerate(surfactants):
            ax_top.bar(iters, grouped[s].values, width=bar_w,
                       bottom=bar_bottoms[j], color=palette[j],
                       alpha=0.88, linewidth=0.3, edgecolor='white',
                       label=s, zorder=3)

        ax_top.set_ylim(0, y_max * 1.28)
        ax_top.set_xlim(x_lo, x_hi)
        ax_top.set_ylabel('Mean Surfactant\nVol (µL)', labelpad=4)
        ax_top.yaxis.grid(True, color='#e0e0e0', linewidth=0.4, zorder=1)
        ax_top.set_axisbelow(True)
        sep_lines(ax_top)
        region_labels(ax_top, y_max * 1.12, y_max * 1.15)
        plt.setp(ax_top.get_xticklabels(), visible=False)

        handles, labels_leg = ax_top.get_legend_handles_labels()
        ax_top.legend(handles[::-1], labels_leg[::-1],
                      title='Surfactant', title_fontsize=FS, fontsize=FS_TICK,
                      loc='upper left', bbox_to_anchor=(1.015, 1.0),
                      borderaxespad=0, handlelength=1.0, handleheight=0.8,
                      labelspacing=0.35, frameon=False)

        # ══ BUBBLE GRID ════════════════════════════════════════════════
        n_surf   = len(surfactants)
        max_val  = grouped.values.max()
        # Largest bubble diameter ≈ 90 % of one row height (in points)
        row_pt   = ax_bot.get_position().height * fig.get_figheight() * 72 / (n_surf + 0.2)
        max_area = (0.9 * row_pt) ** 2

        def to_area(v):
            return (v / max_val) * max_area if max_val > 0 else max_area * 0.5

        draw_region_shading(ax_bot)

        for i in range(n_surf):
            if i % 2 == 0:
                ax_bot.axhspan(i - 0.5, i + 0.5,
                               color='#000000', alpha=0.03, zorder=0, linewidth=0)
        for it in iters:
            ax_bot.axvline(it, color='#e0e0e0', lw=0.4, zorder=1)

        for j, s in enumerate(surfactants):
            for it in iters:
                val = grouped.loc[it, s]
                if pd.notna(val):
                    ax_bot.scatter(it, j, s=to_area(val),
                                   c=palette[j], alpha=0.82,
                                   edgecolors='white', linewidths=0.4, zorder=3)

        sep_lines(ax_bot)
        ax_bot.set_ylim(-0.7, n_surf - 0.5)
        ax_bot.set_xlim(x_lo, x_hi)
        ax_bot.set_yticks(range(n_surf))
        ax_bot.set_yticklabels(surfactants)
        ax_bot.set_xticks(iters)
        ax_bot.set_xticklabels([str(int(it)) for it in iters])
        ax_bot.set_xlabel('Iteration', labelpad=3)
        ax_bot.set_ylabel('Surfactant', labelpad=4)

        title = f"{drug_dict[drug]['full_name']} ({drug_dict[drug]['abbr']})"
        fig.suptitle(title, fontsize=FS_TITLE, y=0.985)

        # ── Panel labels (aligned in figure x) ─────────────────────────
        for ax, label in [(ax_top, 'a)'), (ax_best, 'b)'), (ax_bot, 'c)')]:
            ax.text(0.012, ax.get_position().y1 + 0.012, label,
                    transform=fig.transFigure, fontsize=FS_PANEL,
                    va='bottom', ha='left')

        stem = f'{drug_dict[drug]["abbr"]}_optimization_trace'
        if transparent:
            save_publication_figure(fig, stem, width_cm)
        else:
            os.makedirs('figures', exist_ok=True)
            for ext in ('pdf', 'svg', 'png'):
                fig.savefig(f'figures/{stem}.{ext}', dpi=EXPORT_DPI, facecolor='white')
        plt.show()


import shap
import warnings
from ax.modelbridge.registry import Models
from ax.core.observation import ObservationFeatures
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, LinearSegmentedColormap

warnings.filterwarnings('ignore')

SURF_PARAMS  = list(surfactant_dict.keys())
SURF_DISPLAY = [surfactant_dict[k]['abbr']      for k in SURF_PARAMS]
SURF_FULL    = [surfactant_dict[k]['full_name'] for k in SURF_PARAMS]
TARGET_COL   = 'absorbance'

_SHAP_CMAP = LinearSegmentedColormap.from_list(
    'shap_fv',
    ['#1a4e8a', '#5c9dc7', '#d4e8f5', '#f5f0f0', '#e8a090', '#c0392b', '#7b0f0f'],
    N=512,
)

# Absolute concentration norm: 
_CONC_NORM = Normalize(vmin=0, vmax=200, clip=True)

_RC = {
    'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.linewidth': 0.7,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'xtick.major.size': 3.5, 'ytick.major.size': 0,
    'xtick.labelsize': 10, 'ytick.labelsize': 11,
    'figure.dpi': 150,
}


# ── GP helpers ────────────────────────────────────────────────────────────────

def _build_gp(drug):
    ac = exp_dict[drug]['ax_client']
    return Models.BOTORCH_MODULAR(
        experiment=ac.experiment,
        data=ac.experiment.fetch_data(),
    ), ac


def _get_X_y(drug):
    ac   = exp_dict[drug]['ax_client']
    raw  = ac.get_trials_data_frame()
    done = raw[raw['trial_status'] == 'COMPLETED'].dropna(
        subset=SURF_PARAMS + [TARGET_COL]
    )
    X        = done[SURF_PARAMS].astype(float).values * factor
    y        = done[TARGET_COL].values
    drug_val = done['drug'].iloc[0]
    return X, y, drug_val


def _make_predict_fn(model_bridge, drug_val):
    def predict_fn(X):
        obs = [
            ObservationFeatures(parameters={
                #**dict(zip(SURF_PARAMS, row.tolist())),
                **dict(zip(SURF_PARAMS, (row / factor).tolist())),
                'drug': drug_val,
            })
            for row in np.atleast_2d(X)
        ]
        means, _ = model_bridge.predict(obs)
        return np.array(means[TARGET_COL]).ravel()
    return predict_fn


def _beeswarm_offsets(sv, max_width=0.40, nbins=40):
    n = len(sv)
    offsets = np.zeros(n)
    if n <= 1:
        return offsets
    lo, hi = sv.min(), sv.max()
    span   = hi - lo or 1.0
    edges  = np.linspace(lo - span * 0.01, hi + span * 0.01, nbins + 1)
    bids   = np.clip(np.digitize(sv, edges) - 1, 0, nbins - 1)
    rng    = np.random.default_rng(0)
    for b in np.unique(bids):
        idx = np.where(bids == b)[0]
        k   = len(idx)
        if k == 1:
            continue
        pos = np.zeros(k)
        for i in range(1, k):
            pos[i] = (i // 2 + 1) * (1 if i % 2 == 1 else -1)
        scale = max_width / max(np.abs(pos).max(), 1)
        offsets[idx] = (pos * scale)[rng.permutation(k)]
    return offsets


# ── Panel renderers ───────────────────────────────────────────────────────────

def _draw_shap_panel(fig, ax_bee, ax_cb, shap_values, X, fs=None, ms=40):
    # fs=None keeps the original (screen) sizes; pass e.g. fs=7 for print size
    f_tick, f_lab, f_cb, f_cbt = (11, 10.5, 10, 9) if fs is None else (fs - 0.5, fs, fs, fs - 1)
    n_feat   = len(SURF_PARAMS)
    mean_abs = np.abs(shap_values).mean(axis=0)
    order    = np.argsort(mean_abs)   # ascending → bottom=least important

    for i in range(n_feat):
        ax_bee.axhspan(i - 0.5, i + 0.5,
                       color='#f1f3f8' if i % 2 == 0 else '#ffffff', zorder=0, lw=0)
    for i in range(1, n_feat):
        ax_bee.axhline(i - 0.5, color='#d0d0d0', lw=0.35, zorder=2)
    ax_bee.axvline(0, color='#777777', lw=0.9, zorder=1)

    x_all = []
    for row_idx, feat_idx in enumerate(order):
        sv      = shap_values[:, feat_idx]
        offsets = _beeswarm_offsets(sv, max_width=0.42)
        # Color dots by absolute concentration (µL): 0=blue, 400=white, ≥800=red
        ax_bee.scatter(
            sv, row_idx + offsets,
            c=X[:, feat_idx], cmap=_SHAP_CMAP, norm=_CONC_NORM,
            s=ms, alpha=0.85, edgecolors='white', linewidths=0.7 * (ms / 40) ** 0.5, zorder=3,
        )
        x_all.extend(sv.tolist())

    x_abs = np.abs(x_all).max() * 1.08
    ax_bee.set_xlim(-x_abs, x_abs)
    ax_bee.set_ylim(-0.5, n_feat - 0.5)
    ax_bee.xaxis.grid(True, color='#e0e0e0', lw=0.4, zorder=0)
    ax_bee.set_axisbelow(True)
    for sp in ['top', 'right', 'left']:
        ax_bee.spines[sp].set_visible(False)
    ax_bee.spines['bottom'].set_color('#888888')
    ax_bee.set_yticks(range(n_feat))
    ax_bee.set_yticklabels([SURF_DISPLAY[order[i]] for i in range(n_feat)], fontsize=f_tick)
    ax_bee.tick_params(axis='y', length=0, pad=6)
    ax_bee.set_xlabel('SHAP value  (impact on predicted absorbance)', fontsize=f_lab, labelpad=4)

    # Colorbar styled the same as the surface colorbar
    sm = ScalarMappable(cmap=_SHAP_CMAP, norm=_CONC_NORM)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=ax_cb)
    cbar.set_label('Surfactant conc. (µL)', fontsize=f_cb)
    cbar.set_ticks([0, 100, 200])
    cbar.set_ticklabels(['0', '100', '200'])
    cbar.ax.tick_params(labelsize=f_cbt, length=2.5, width=0.5, pad=4)
    cbar.outline.set_linewidth(0.5)
    cbar.solids.set_rasterized(False)   # matplotlib rasterizes >50-colour bars by default


def _draw_surface_panel(fig, ax, ax_cb, Z, F0, F1, X, y, idx_x, idx_y, feat_x, feat_y,
                        fs=None, ms=40):
    # fs=None keeps the original (screen) sizes; pass e.g. fs=7 for print size
    f_lab, f_cb, f_cbt = (10.5, 10, 9) if fs is None else (fs, fs, fs - 1)
    norm = Normalize(vmin=0, vmax=1, clip=True)
    pm   = ax.pcolormesh(F0, F1, Z, cmap=_SHAP_CMAP, norm=norm, shading='gouraud')
    cbar = fig.colorbar(pm, cax=ax_cb) if ax_cb is not None else fig.colorbar(pm, ax=ax)
    cbar.set_label('Predicted absorbance (GP)', fontsize=f_cb)
    cbar.set_ticks([0, 0.5, 1])
    cbar.set_ticklabels(['0', '0.5', '1'])
    cbar.ax.tick_params(labelsize=f_cbt, length=2.5, width=0.5, pad=4)
    cbar.outline.set_linewidth(0.5)
    cbar.solids.set_rasterized(False)   # matplotlib rasterizes >50-colour bars by default
    ax.scatter(X[:, idx_x], X[:, idx_y], c=y, cmap=_SHAP_CMAP, norm=norm,
               edgecolors='k', linewidths=0.5 * (ms / 40) ** 0.5, s=ms, zorder=5, clip_on=False, label='Observed')
    ax.set_xlabel(f'{feat_x} (µL)', fontsize=f_lab, labelpad=3 if fs else 6)
    ax.set_ylabel(f'{feat_y} (µL)', fontsize=f_lab, labelpad=3 if fs else 6)
    # ax.legend(fontsize=8)
    # for sp in ['top', 'right']:
    #     ax.spines[sp].set_visible(False)


def _top_shap_features(shap_values, feat_x, feat_y):
    mean_abs = np.abs(shap_values).mean(axis=0)
    top_idx  = np.argsort(mean_abs)[::-1]
    feat_x   = feat_x or SURF_DISPLAY[top_idx[0]]
    feat_y   = feat_y or SURF_DISPLAY[top_idx[1]]
    return feat_x, feat_y


def _compute_surface_grid(predict_fn, X, y, idx_x, idx_y, gs=40):
    base     = X[np.argmin(y)]
    f0_vals  = np.linspace(X[:, idx_x].min(), X[:, idx_x].max(), gs)
    f1_vals  = np.linspace(X[:, idx_y].min(), X[:, idx_y].max(), gs)
    F0, F1   = np.meshgrid(f0_vals, f1_vals)
    grid_pts = np.tile(base, (gs * gs, 1))
    grid_pts[:, idx_x] = F0.ravel()
    grid_pts[:, idx_y] = F1.ravel()
    Z = predict_fn(grid_pts).reshape(gs, gs)
    return F0, F1, Z


# ── Public API ────────────────────────────────────────────────────────────────

def plot_shap(drug):
    print(f"[{drug}] Fitting GP...", flush=True)
    model_bridge, _ = _build_gp(drug)
    X, y, drug_val  = _get_X_y(drug)
    predict_fn      = _make_predict_fn(model_bridge, drug_val)
    background      = shap.kmeans(X, min(10, len(X)))
    explainer       = shap.KernelExplainer(predict_fn, background)
    print(f"[{drug}] Computing SHAP ({len(X)} × {len(SURF_PARAMS)})...", flush=True)
    shap_values     = explainer.shap_values(X, silent=True)

    with plt.rc_context(_RC):
        fig    = plt.figure(figsize=(7.5, 5.8), facecolor='white')
        ax_bee = fig.add_axes([0.18, 0.12, 0.66, 0.76])
        ax_cb  = fig.add_axes([0.87, 0.12, 0.025, 0.76])
        _draw_shap_panel(fig, ax_bee, ax_cb, shap_values, X)
        fig.text(0.50, 0.958,
                 f'{drug_dict[drug]["full_name"]} ({drug})\u2002\u2014\u2002SHAP Feature Importance',
                 ha='center', va='top', fontsize=12.5, fontweight='semibold', color='#1a1a1a')
        os.makedirs('figures', exist_ok=True)
        save_path = f'figures/shap_{drug}.png'
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.show()
        print(f"  saved → {save_path}")
    return shap_values


def plot_response_surface(drug, feat_x=None, feat_y=None):
    print(f"[{drug}] Fitting GP...", flush=True)
    model_bridge, _ = _build_gp(drug)
    X, y, drug_val  = _get_X_y(drug)
    predict_fn      = _make_predict_fn(model_bridge, drug_val)

    if feat_x is None or feat_y is None:
        background  = shap.kmeans(X, min(10, len(X)))
        explainer   = shap.KernelExplainer(predict_fn, background)
        print(f"[{drug}] Computing SHAP for top-feature selection...", flush=True)
        shap_values = explainer.shap_values(X, silent=True)
        feat_x, feat_y = _top_shap_features(shap_values, feat_x, feat_y)

    idx_x = SURF_DISPLAY.index(feat_x)
    idx_y = SURF_DISPLAY.index(feat_y)
    print(f"[{drug}] Predicting surface ({feat_x} × {feat_y})...", flush=True)
    F0, F1, Z = _compute_surface_grid(predict_fn, X, y, idx_x, idx_y)

    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(6, 5), facecolor='white')
        ax.set_title(
            f'{drug_dict[drug]["full_name"]} ({drug})\nGP response surface: {feat_x} vs {feat_y}',
            fontsize=11,
        )
        _draw_surface_panel(fig, ax, None, Z, F0, F1, X, y, idx_x, idx_y, feat_x, feat_y)
        fig.tight_layout()
        os.makedirs('figures', exist_ok=True)
        save_path = f'figures/response_surface_{drug}.png'
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.show()
        print(f"  saved → {save_path}")



def plot_drug(drug, feat_x=None, feat_y=None, shap_plot=0):
    """Plot GP response surface, optionally with SHAP beeswarm."""
    print(f"[{drug}] Fitting GP...", flush=True)
    model_bridge, _ = _build_gp(drug)
    X, y, drug_val  = _get_X_y(drug)
    predict_fn      = _make_predict_fn(model_bridge, drug_val)

    background  = shap.kmeans(X, min(10, len(X)))
    explainer   = shap.KernelExplainer(predict_fn, background)
    print(f"[{drug}] Computing SHAP ({len(X)} × {len(SURF_PARAMS)})...", flush=True)
    shap_values = explainer.shap_values(X, silent=True)

    feat_x, feat_y = _top_shap_features(shap_values, feat_x, feat_y)
    idx_x = SURF_DISPLAY.index(feat_x)
    idx_y = SURF_DISPLAY.index(feat_y)
    print(f"[{drug}] Predicting surface ({feat_x} × {feat_y})...", flush=True)
    F0, F1, Z = _compute_surface_grid(predict_fn, X, y, idx_x, idx_y)

    # Print sizes: single column (8.5 cm) for the surface alone,
    # double column (17.8 cm) when the SHAP beeswarm is added.
    FS = 7.0
    rc = {**_RC, 'font.size': FS, 'axes.linewidth': 0.6,
          'xtick.labelsize': FS - 0.5, 'ytick.labelsize': FS - 0.5,
          'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
          'xtick.major.width': 0.6, 'ytick.major.width': 0.6}

    with plt.rc_context(rc):
        if shap_plot == 1:
            width_cm, height_cm = DOUBLE_COL_CM, 7.5
            fig = plt.figure(figsize=(width_cm * CM, height_cm * CM))
            ax_bee     = fig.add_axes([0.075, 0.14, 0.34, 0.70])
            ax_cb_shap = fig.add_axes([0.425, 0.14, 0.012, 0.70])
            ax_surf    = fig.add_axes([0.56, 0.14, 0.31, 0.70])
            ax_cb_surf = fig.add_axes([0.885, 0.14, 0.012, 0.70])

            _draw_shap_panel(fig, ax_bee, ax_cb_shap, shap_values, X, fs=FS, ms=10)

            for ax_, lab in [(ax_bee, 'a)'), (ax_surf, 'b)')]:
                ax_.text(-0.08, 1.03, lab, transform=ax_.transAxes,
                         fontsize=8, va='bottom', color='#1a1a1a')

            ax_bee.set_title('SHAP Feature Importance', fontsize=FS,
                             pad=5, color='#333333')
            title_x = 0.48
        else:
            width_cm, height_cm = SINGLE_COL_CM, 7.4
            fig = plt.figure(figsize=(width_cm * CM, height_cm * CM))
            ax_surf    = fig.add_axes([0.155, 0.135, 0.60, 0.70])
            ax_cb_surf = fig.add_axes([0.785, 0.135, 0.03, 0.70])
            title_x = 0.485

        _draw_surface_panel(fig, ax_surf, ax_cb_surf, Z, F0, F1,
                            X, y, idx_x, idx_y, feat_x, feat_y, fs=FS, ms=10)

        ax_surf.set_title(f'GP Response Surface: {feat_x} vs {feat_y}',
                          fontsize=FS, pad=5, color='#333333')

        fig.suptitle(
            f'{drug_dict[drug]["full_name"]} ({drug})',
            fontsize=8, color='#1a1a1a', y=0.975, x=title_x,
        )

        save_publication_figure(fig, f'model_analysis_{drug}', width_cm)
        plt.show()