"""Offline LOD0 preview using same-entity Look/material bindings; no global texture guess.

Usage: .venv/Scripts/python.exe tools/preview_asset_meshes.py output.jpg ENTITY...
Only reads cache files. Unknown color bindings are neutral grey and labelled.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw

CACHE=Path(__file__).resolve().parents[1]/'research/asset-cache'


def rasterize(positions,normals,uv,triangles,texture_ids,textures,azimuth,elevation,width=192,height=248):
    a,e=np.radians(azimuth),np.radians(elevation)
    rotation=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    tilt=np.array([[1,0,0],[0,np.cos(e),-np.sin(e)],[0,np.sin(e),np.cos(e)]])
    view=positions@rotation.T@tilt.T
    normal=normals@rotation.T@tilt.T
    scale=min(width*.44/max(1e-6,abs(view[:,0]).max()),height*.44/max(1e-6,abs(view[:,1]).max()))
    screen=np.stack([width/2+view[:,0]*scale,height/2-view[:,1]*scale],axis=1)
    color=np.full((height,width,3),(40,40,48),dtype=np.uint8)
    depth=np.full((height,width),-np.inf)
    for triangle,texture_id in zip(triangles,texture_ids):
        points=screen[triangle]
        x0,y0=np.floor(points.min(0)).astype(int)
        x1,y1=np.ceil(points.max(0)).astype(int)
        x0,y0=max(0,x0),max(0,y0)
        x1,y1=min(width-1,x1),min(height-1,y1)
        if x0>x1 or y0>y1:
            continue
        p,q,r=points
        denominator=(q[1]-r[1])*(p[0]-r[0])+(r[0]-q[0])*(p[1]-r[1])
        if abs(denominator)<1e-8:
            continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1]+.5
        b0=((q[1]-r[1])*(xx-r[0])+(r[0]-q[0])*(yy-r[1]))/denominator
        b1=((r[1]-p[1])*(xx-r[0])+(p[0]-r[0])*(yy-r[1]))/denominator
        bary=np.stack([b0,b1,1-b0-b1],axis=-1)
        z=bary@view[triangle,2]
        visible=(bary.min(-1)>=-1e-6)&(z>depth[y0:y1+1,x0:x1+1])
        if not visible.any():
            continue
        texture=textures.get(texture_id)
        if texture is None:
            pixels=np.full(bary.shape[:2]+(3,),180.)
        else:
            coords=(bary@uv[triangle])%1
            th,tw=texture.shape[:2]
            pixels=texture[np.minimum(th-1,(coords[:,:,1]*th).astype(int)),np.minimum(tw-1,(coords[:,:,0]*tw).astype(int))].astype(float)
        light=.35+.65*np.abs(bary@normal[triangle,2])
        pixels=np.clip(pixels*light[:,:,None],0,255).astype(np.uint8)
        color[y0:y1+1,x0:x1+1][visible]=pixels[visible]
        depth[y0:y1+1,x0:x1+1][visible]=z[visible]
    return Image.fromarray(color)


def render(entity,size=192):
    directory=CACHE/entity
    chain=json.loads((directory/'chain.json').read_text(encoding='utf-8'))
    roots=[r['guid'] for r in chain['resources'].get(entity,{}).get('refs',[]) if r['guid'].startswith('0d00')]
    models=[g for g in roots if chain['resources'].get(g,{}).get('model',{}).get('status')=='parsed']
    image=Image.new('RGB',(size*2,296),(40,40,48))
    draw=ImageDraw.Draw(image)
    if not models:
        draw.text((6,6),entity+' no LOD0 mesh',fill='red')
        return image
    mesh=json.loads((directory/chain['resources'][models[0]]['model']['file']).read_text(encoding='utf-8'))
    if mesh.get('lod')!=0 or 'triangleTextureIds' not in mesh:
        raise ValueError('Refresh chain with corrected LOD0 parser before preview: '+entity)
    positions=np.asarray(mesh['positions']).reshape(-1,3)
    normals=np.asarray(mesh['normals']).reshape(-1,3)
    uv=np.asarray(mesh['uv']).reshape(-1,2)
    triangles=np.asarray(mesh['indices']).reshape(-1,3)
    texture_ids=mesh['triangleTextureIds']
    if len(texture_ids)!=len(triangles):
        raise ValueError('Triangle/material array length mismatch')
    positions=positions-(positions.min(0)+positions.max(0))/2
    textures={}
    for submesh in mesh['submeshes']:
        binding=submesh['binding']
        if binding['status']=='bound':
            if binding['format'] not in (72,78):
                raise ValueError('Non-sRGB texture cannot be used as color')
            with Image.open(directory/binding['textureFile']) as texture:
                textures[binding['colorTexture']]=np.asarray(texture.convert('RGB'))
    for i,(azimuth,elevation) in enumerate(((35,30),(215,65))):
        image.paste(rasterize(positions,normals,uv,triangles,texture_ids,textures,azimuth,elevation,size,248),(i*size,22))
    draw.text((6,5),f'{entity[-4:]} LOD0 {len(positions)}v / {len(triangles)}t',fill='white')
    colors=sorted(set(t for t in texture_ids if t))
    draw.text((6,275),'sRGB: '+', '.join(t[-4:] for t in colors)+(' | UNRESOLVED: grey' if None in texture_ids else ''),fill='yellow')
    return image


def main():
    out,*entities=sys.argv[1:]
    if not entities:
        raise SystemExit('Expected output JPEG and at least one entity GUID')
    tiles=[render(entity) for entity in entities]
    columns=min(2,len(tiles))
    sheet=Image.new('RGB',(384*columns,296*math.ceil(len(tiles)/columns)),(40,40,48))
    for i,tile in enumerate(tiles):
        sheet.paste(tile,((i%columns)*384,(i//columns)*296))
    sheet.thumbnail((768,768))
    sheet.save(out,quality=80)
    print(json.dumps({'file':out,'size':list(sheet.size),'entities':entities}))


if __name__=='__main__':
    main()
