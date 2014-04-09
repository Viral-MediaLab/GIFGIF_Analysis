import Image, ImageDraw

def get_colors(infile, outfile, numcolors=1, swatchsize=20, resize=150):
    # Gist from Stefan Zollinger on Github: 
    # https://gist.github.com/zollinger/1722663
    image = Image.open(infile)
    image = image.resize((resize, resize))
    result = image.convert('P', palette=Image.ADAPTIVE, colors=numcolors)
    result.putalpha(0)
    colors = result.getcolors(resize*resize)
    print colors
    # Save colors to file
    pal = Image.new('RGB', (swatchsize*numcolors, swatchsize))
    draw = ImageDraw.Draw(pal)
    posx = 0
    for count, col in colors:
        draw.rectangle([posx, 0, posx+swatchsize, swatchsize], fill=col)
        posx = posx + swatchsize
    del draw
    pal.save(outfile, "PNG")


# infile = '../../../giffig_misc/what/gifs/2CsCSsHqPVcNa_still.gif'
get_colors(infile, 'outfile.png')


def returnDominant(infile, numcolors=1):
    image = Image.open(infile)
    result = image.convert('P', palette=Image.ADAPTIVE, colors=numcolors)
    result.putalpha(0)
    colors = result.getcolors()
    print colors
    return colors[0][1]


''''
Possible result Ideas:
1) Color distribution per emotion. With 0.5 as the 'even' mark, sum the dominant colors and scale by their rating for that given emotion
    Represent it as a 3D color wheel, with varying heights?
2) Place the average color per emotion on a color wheel. Take the top 50 global from each category, sum their average colors. and put on wheel.
3) 

''''