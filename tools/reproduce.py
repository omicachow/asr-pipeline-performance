"""Recompute the public statistics and figures. No audio, GPU, network or private paths."""
from pathlib import Path
import argparse, csv, hashlib, math, re

ROOT = Path(__file__).resolve().parents[1]
RUNS = list(csv.DictReader((ROOT/'data/runs.csv').read_text(encoding='utf-8').splitlines()))
PAIRS = list(csv.DictReader((ROOT/'data/paired_summary.csv').read_text(encoding='utf-8').splitlines()))

def num(row,key):
    return float(row[key]) if row.get(key) not in ('',None) else None

def mean(rs,key):
    vals=[num(r,key) for r in rs]
    if any(v is None for v in vals): return None
    return sum(vals)/len(vals)

def pick(experiment,recording=None,version=None):
    return [r for r in RUNS if r['experiment']==experiment and
            (recording is None or r['recording']==recording) and
            (version is None or r['version']==version)]

def check():
    assert len(RUNS)==80, len(RUNS)
    for r in RUNS:
        a,w=num(r,'audio_seconds'),num(r,'worker_seconds')
        assert a>0 and w>0
        assert math.isclose(num(r,'worker_audio_seconds_per_second'),a/w,rel_tol=1e-10)
        c=num(r,'client_seconds')
        if c is not None: assert math.isclose(num(r,'client_audio_seconds_per_second'),a/c,rel_tol=1e-10)
    for p in PAIRS:
        a=pick(p['experiment'],p['recording'],p['baseline'])
        b=pick(p['experiment'],p['recording'],p['candidate'])
        assert len(a)==len(b)==int(p['n_each'])
        for k in ['worker','client']:
            av,bv=mean(a,k+'_seconds'),mean(b,k+'_seconds')
            if av is None:
                assert not p['baseline_'+k+'_seconds']
                continue
            assert math.isclose(av,num(p,'baseline_'+k+'_seconds'),rel_tol=1e-12)
            assert math.isclose(bv,num(p,'candidate_'+k+'_seconds'),rel_tol=1e-12)
            assert math.isclose(1-bv/av,num(p,k+'_reduction_fraction'),abs_tol=1e-12)
    for r in pick('E06')+pick('E07'):
        pre=num(r,'pre_community_critical_path_seconds')
        if pre is not None:
            accounted=pre+num(r,'community_outer_seconds')+num(r,'after_community_critical_path_seconds')
            assert math.isclose(accounted,num(r,'worker_seconds'),abs_tol=.02)
    article=(ROOT/'README.md').read_text(encoding='utf-8')
    assert '{{' not in article, 'Unfilled article table'
    for ref in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',article):
        if ref.startswith(('https://','#')): continue
        assert (ROOT/ref).is_file(),ref
    for p in [ROOT/'README.md',ROOT/'METHODS.md']:
        s=p.read_text(encoding='utf-8')
        assert not re.search(r'(?i)(?:(?<![A-Z])[A-Z]:[\\/]|/home/|192\.168\.|10\.\d+\.\d+\.\d+|rq_[a-f0-9]{20})',s),p
    for line in (ROOT/'checksums.sha256').read_text(encoding='utf-8').splitlines():
        sha,name=line.split('  ',1)
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    print(f'PASS: {len(RUNS)} observations, {len(PAIRS)} comparisons, critical paths, article links and checksums.')
    for p in PAIRS:
        client=num(p,'client_reduction_fraction')
        c=f'{client*100:.2f}%' if client is not None else 'not available'
        print(f"{p['experiment']} {p['recording']} {p['baseline']} -> {p['candidate']}: "
              f"Worker {num(p,'worker_reduction_fraction')*100:.2f}% less; client {c} less")

def plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.titleweight':'bold','savefig.facecolor':'white',
                         'figure.facecolor':'white','axes.facecolor':'white','svg.fonttype':'path'})
    A=ROOT/'assets';A.mkdir(exist_ok=True)
    blue,orange,gray='#225C79','#C47235','#607888'
    def save(fig,name):
        fig.savefig(A/(name+'.png'),dpi=180,bbox_inches='tight',metadata={'Software':'Matplotlib'})
        plt.close(fig)

    fig,axs=plt.subplots(2,2,figsize=(12,7.3),layout='constrained')
    for ax,exp in zip(axs.flat,['E02','E03','E05','E06']):
        p=next(x for x in PAIRS if x['experiment']==exp)
        versions=[p['baseline'],p['candidate']]
        ww=[num(p,'baseline_worker_seconds'),num(p,'candidate_worker_seconds')]
        cc=[num(p,'baseline_client_seconds'),num(p,'candidate_client_seconds')]
        for j,v in enumerate(versions):
            for offset,vals,color,label in [(-.16,ww,blue,'Worker'),(.16,cc,orange,'Client')]:
                yy=j+offset
                ax.barh(yy,vals[j],height=.27,color=color,label=label if j==0 else None)
                ax.text(vals[j]+max(cc)*.015,yy,f'{vals[j]:.1f}',va='center',fontsize=10)
                samples=pick(exp,'L193',v)
                if len(samples)>1:
                    key='worker_seconds' if offset<0 else 'client_seconds'
                    for r in samples: ax.plot(num(r,key),yy,'|',color='#142D3B',markersize=11)
        ax.set_yticks([0,1],versions);ax.invert_yaxis();ax.set_xlim(0,max(cc)*1.17)
        ax.set_xlabel('Wall-clock seconds (lower is better)')
        ax.set_title(f"{exp}: {versions[0]} / {versions[1]} | L193 | n={p['n_each']} each",fontsize=11)
        ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
    fig.suptitle('Four separate same-recording comparisons',fontsize=17,fontweight='bold')
    handles,labels=axs.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,-.055),ncol=2,frameon=False)
    save(fig,'paired-comparisons')

    rr=pick('E04','A54')
    fig,ax=plt.subplots(figsize=(10,5.2),layout='constrained')
    xs=list(range(len(rr)))
    for j,r in enumerate(rr):
        ax.bar(j-.18,num(r,'worker_seconds'),width=.34,color=blue,label='Worker total' if j==0 else None)
        ax.bar(j+.18,num(r,'retry_model_reported_seconds'),width=.34,color=orange,
               label='Successful recovery inference (inside Worker)' if j==0 else None)
        for xx,key in [(j-.18,'worker_seconds'),(j+.18,'retry_model_reported_seconds')]:
            ax.text(xx,num(r,key)+10,f'{num(r,key):.1f}',ha='center',fontsize=10)
    ax.set_xticks(xs,[r['version'] for r in rr]);ax.set_ylim(0,810)
    ax.set_ylabel('Seconds');ax.set_title('A54: expensive retry tails dominate the task',pad=15)
    ax.legend(frameon=False,loc='upper right',fontsize=9);ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
    fig.text(.02,-.015,'One fresh run per version. Recovery bars are nested measurements, not additional time.',fontsize=9,color=gray)
    save(fig,'recovery-tail')

    rr=pick('E07')
    fig,ax=plt.subplots(figsize=(10,5.8),layout='constrained')
    for j,r in enumerate(rr):
        for d,key,c,label in [(-.16,'worker_audio_seconds_per_second',blue,'Worker'),
                              (.16,'client_audio_seconds_per_second',orange,'Client incl. transfers')]:
            ax.barh(j+d,num(r,key),height=.28,color=c,label=label if j==0 else None)
            ax.text(num(r,key)+.5,j+d,f'{num(r,key):.2f}x',va='center',fontsize=10)
    labels=[f"{r['recording']}{' repeat' if r['replicate']=='2' else ''}  ({num(r,'audio_seconds')/60:.2f} min)" for r in rr]
    ax.set_yticks(list(range(len(rr))),labels);ax.invert_yaxis();ax.set_xlim(0,58)
    ax.set_xlabel('Audio seconds processed per wall-clock second (higher is better)')
    ax.set_title('R22: four additional full recordings + one repeat',pad=16)
    ax.legend(loc='lower right',frameon=False);ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
    fig.text(.02,-.015,'Different recordings, not version A/B tests. No human accuracy reference is available.',fontsize=9,color=gray)
    save(fig,'stability')

    fig,ax=plt.subplots(figsize=(12,5.4),layout='constrained');ax.set_xlim(0,12);ax.set_ylim(0,5.2);ax.axis('off')
    def box(x,y,w,h,label,color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.05,rounding_size=0.1',
                                   facecolor=color,edgecolor='#D6E1E7',linewidth=1))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10,color='#17384A')
    def arrow(x1,y1,x2,y2):
        ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=15,color=gray,linewidth=1.4))
    ax.text(.1,4.85,'Full long-form transcription, including alignment and speakers',fontsize=17,fontweight='bold')
    box(.1,3.45,2.0,.85,'Client\nUpload full MP3','#FAECDD')
    box(2.7,3.45,2.3,.85,'Decode once\n16 kHz mono + split','#E5F0F5');arrow(2.15,3.87,2.65,3.87)
    box(5.6,3.45,3.1,.85,'Qwen3-ASR list batches\n+ grouped alignment RPCs','#E5F0F5');arrow(5.05,3.87,5.55,3.87)
    box(9.3,3.45,2.5,.85,'Community-1\nFull / Exclusive','#E5F0F5');arrow(8.75,3.87,9.25,3.87)
    box(9.3,1.9,2.5,.85,'Word / speaker fusion\nQuality flags + schema','#E5F0F5');arrow(10.55,3.4,10.55,2.8)
    box(5.6,1.9,3.1,.85,'Lossless result bundle\nManifest + verification','#E5F0F5');arrow(9.25,2.32,8.75,2.32)
    box(.1,1.9,4.9,.85,'Client download + verification + ACK\nOriginal audio remains private','#FAECDD');arrow(5.55,2.32,5.05,2.32)
    ax.plot([2.7,11.8],[1.5,1.5],color=blue,linewidth=2)
    ax.text(7.25,1.17,'Worker clock: excludes upload / download',ha='center',fontsize=10,color=blue)
    ax.plot([.1,11.8],[.72,.72],color=orange,linewidth=2)
    ax.text(6,.35,'Client clock: complete submit-to-result flow',ha='center',fontsize=10,color=orange)
    save(fig,'pipeline')
    print('Wrote four PNG figures.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check: check()
    else: plots()

if __name__=='__main__': main()
