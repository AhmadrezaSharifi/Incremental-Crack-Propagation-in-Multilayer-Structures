from abaqus import *
from abaqusConstants import *
from caeModules import *
# Import Python packages
import numpy as np
import math
import os
model_name='mx_1'
# Define your description
description = 'matrix'
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
####################################################
# Input Parameters
# parameters for geometry, material, load and mesh (N-m1-s)
####################################################
# Geometry
# Specimen and simulation parameters------------------------------------
s_th  = 6.0                 #Spicement thickness 
s_l   = 65.0                #Spicement length
s_h   = 14.0                #Spicement hight
n_l   = 0.1                 #Creack width
n_h   = 2.0                 #Crack higth
m_s   = 0.2                 #Elemenet size
ct_ms = 0.2                 #Elemenet size on crack path
b_r   = 5.0                 #Cylender radios
sout  = 4.5                 #Cylender center to spicement edge
TOL   = 1e-5                #Tolerence
fc    = 0.0                 #Friction coeficient

intr_lyr_pr = (6.2, 0.48)       #Interlayer Elastic behavior (E,nu)
matrix_pr   = (2029.0, 0.42)    #Matrix behavior (E,nu)

g_c1   = 0.0858                 #Matrix fracture toughness
g_c2   = 0.0429                 #Interface fracture toughness           
sig_c  = 90                     #Yield stress

disp_inc=0.02                   #Displacement increament
disp_lim = 2.8                   #Total displacmenet limitation

#Plastic stress strain table
matrix_plastic_data = [
    (70.0000, 0.000000),
    (74.5000, 0.02500),
    (80.0000, 0.06000),
    (86.0000, 0.12000),
    (92.0000, 0.20000),
    (98.5000, 0.30000),
    (107.0000, 0.42000),
    (113.5000, 0.52000),
    (118.0000, 0.60000),
    (122.5000, 0.70000),
    (125.0000, 0.80000)
]

# Calculating Neo-Hookean material constants
Eh= intr_lyr_pr[0]
nuh = intr_lyr_pr[1]
mu = Eh / (2 * (1 + nuh))
C10 = mu / 2
K = Eh / (3 * (1 - 2 * nuh))
D1 = 2 / K


# Derived parameters (as in original code)
x_r = (-s_l / 2, s_l / 2)
g_c = g_c1

# Change working directory-----------------------------------------------
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))  # go one level up
full_path = os.path.join(parent_dir, model_name)

# Create the folder in the parent directory if it doesn't exist
if not os.path.exists(full_path):
    os.makedirs(full_path)

# Change directory: go up one level and into the model folder
os.chdir("../" + model_name)

# save the input paramatesr into seprated file in directory directio
# Now save the current values to a text file
with open("input_parameters.txt", "w") as f:
    f.write("Input Parameters\n")
    f.write("\nSpecimen and simulation parameters:\n")
    f.write("s_th = {}\n".format(s_th))
    f.write("s_l = {}\n".format(s_l))
    f.write("s_h = {}\n".format(s_h))
    f.write("n_l = {}\n".format(n_l))
    f.write("n_h = {}\n".format(n_h))
    f.write("m_s = {}\n".format(m_s))
    f.write("ct_ms = {}\n".format(ct_ms))
    f.write("b_r = {}\n".format(b_r))
    f.write("sout = {}\n".format(sout))
    f.write("TOL = {}\n".format(TOL))
    f.write("fc = {}\n".format(fc))
    f.write("\nMaterial properties:\n")
    f.write("intr_lyr_pr = {}\n".format(intr_lyr_pr))
    f.write("matrix_pr = {}\n".format(matrix_pr))
    f.write("gm_c[0] = {}\n".format(g_c1))
    f.write("gi_cI= {}\n".format(g_c2))
    f.write("sig_c = {}\n".format(sig_c))
# Write the description to the file
with open('model_description.txt', 'w') as file:
    file.write(description)
#create model
Mdb()
model = mdb.models['Model-1']
# required functions------------------------------------------------------  


# Create material
def create_material( material_name, elastic_properties,p):
    model.Material(name=material_name)
    model.materials[material_name].Elastic(table=(elastic_properties,))
    model.HomogeneousSolidSection(
        name=material_name+'_sec',material=material_name,)
    p.SectionAssignment( region=p.sets[material_name], sectionName=material_name+'_sec')
    model.sections[material_name+'_sec'].setValues(material=material_name, 
        thickness=s_th)
# Assembly
asmb=model.rootAssembly
ins = asmb.instances
def create_instance(partname):

    asmb.Instance(dependent=OFF,name=partname+'-1',part=model.parts[partname])

    return

# Steps 
def create_static_step( previous_step, step_name, initial_inc, max_inc):
    model.StaticStep(initialInc=initial_inc,maxInc=max_inc, name=step_name, nlgeom=ON, 
        previous=previous_step)
    model.steps[step_name].Restart(frequency=1)
    return
def get_energy_release_rate(st_n, da):
    hr2 = odb.steps[st_n].historyRegions['Assembly ASSEMBLY'].historyOutputs['ALLSE']
    hr3 = odb.steps[st_n].historyRegions['Assembly ASSEMBLY'].historyOutputs['ALLFD']
    ALLSE1 = 2*(hr2.data[0][-1])
    ALLSE2 = 2*(hr2.data[-1][-1])
    ALLFD1 = 2*(hr3.data[0][-1])
    ALLFD2 = 2*(hr3.data[-1][-1])
    g = (-(ALLSE2 - ALLSE1)+(ALLFD2-ALLFD1)) / (s_th * da)
    hr_l=odb.steps[st_n].historyRegions.keys()
    rp_l=[item for item in hr_l if 'Node' in item]
    rf2 = odb.steps[st_n].historyRegions[rp_l[0]].historyOutputs['RF2'].data
    ru2=   odb.steps[st_n].historyRegions[rp_l[0]].historyOutputs['U2'].data
    rf2l = -2*rf2[0][1]
    ru2l = -ru2[0][1]
    # print('g:', g)
    return g,rf2l,ru2l



def adpt_disp(disp):

    disp=disp+disp_inc

    return disp


def export_field_images(jb_n, st_n):

    
    # Get the last frame of the specified step
    odb_st = odb.steps[st_n]
    # Open the viewport and set the displayed object & deformation form
    vp = session.viewports['Viewport: 1']
    vp.restore()
    vp.setValues(origin=(0,0))
    vp.setValues(width=300,height=200)
    vp.view.fitView()
    vp.setValues(displayedObject=odb)
    ss_disp=vp.odbDisplay
    vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))

    # Set primary variable to Mises stress Set to last frame
    vp.odbDisplay.setPrimaryVariable(variableLabel='S',outputPosition=INTEGRATION_POINT,refinement=(INVARIANT, 'Mises'))
    vp.odbDisplay.setFrame(step=st_n, frame=len(odb_st.frames) - 1)

    #Mirering & Hide mesh  & Fit view to part 
    ss_disp.basicOptions.setValues(mirrorAboutYzPlane=True)
    vp.odbDisplay.commonOptions.setValues(visibleEdges=FREE)
    vp.view.fitView()
    vp.viewportAnnotationOptions.setValues(title=OFF,state=OFF, annotations=OFF, compass=OFF)
    vp.viewportAnnotationOptions.setValues(legendBackgroundStyle=OTHER, legendBackgroundColor='#FFFFFF')

    # Optional: save image (e.g., PNG)
    session.printOptions.setValues(rendition=COLOR, vpDecorations=OFF, compass=OFF,reduceColors=True)
    session.printToFile(fileName='../'+model_name+'/mises_'+jb_n ,format=PNG,canvasObjects=(vp,))

    
    # Save deformation magnitude plot
    ss_disp.setPrimaryVariable(variableLabel='U', outputPosition=NODAL, refinement=(INVARIANT, 'Magnitude'), )
    session.printToFile(fileName='../'+model_name+'/umag_'+jb_n ,format=PNG,canvasObjects=(vp,))

    return
#
# Delete unwanted files----------------------------------------------------
def delete_files():
    keep_exts = ['.inp', '.odb', '.cae' , '.py', '.pyc', '.txt', '.png']  #the file format that you want to keep

    # Get current directory
    current_dir = os.getcwd()

    # Loop over files in the directory
    for filename in os.listdir(current_dir):
        file_path = os.path.join(current_dir, filename)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(filename)
            if ext not in keep_exts:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print('Could not delete {}: {}'.format(filename, e))

    return


def get_max_principal(st_n):
    matrix_set = odb.rootAssembly.elementSets['ALL']  


    matrix_labels = set(e.label for elset in matrix_set.elements for e in elset)

    stress_field = odb.steps[st_n].frames[-1].fieldOutputs['S']
    max_p_matrix = -1e20
    max_p_intr_lyr = -1e20

    for v in stress_field.values:
        if v.elementLabel in matrix_labels:
            if v.maxPrincipal > max_p_matrix:
                max_p_matrix = v.maxPrincipal
    return max_p_matrix

# main script-----------------------------------------------------------
# Create parts-----------------------------------------------------------
s= model.ConstrainedSketch(name='base_shell', sheetSize=200.0)
s.Line(point1=(0.0, s_h)    , point2=(0.0, n_h))
s.Line(point1=(0.0, n_h)    , point2=(n_l/2, 0.0))
s.Line(point1=(n_l/2, 0.0)  , point2=(s_l/2, 0.0))
s.Line(point1=(s_l/2, 0.0)  , point2=(s_l/2, s_h))
s.Line(point1=(s_l/2, s_h)  , point2=(0.0, s_h))
# Create base_shell
p=model.Part(dimensionality=TWO_D_PLANAR, name='base_shell', type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)

p.Set           (name='all'         , faces=p.faces[:])
p.Set           (name='eg_xsym2'    , edges=p.edges.getByBoundingBox(xMax=TOL))
p.Surface       (name='bt_cnt'      , side1Edges=p.edges.getByBoundingBox(yMax=TOL))
p.Surface       (name='up_cnt'      , side1Edges=p.edges.getByBoundingBox(yMin=s_h))
p.Set           (name='matrix'         , faces=p.faces[:])

# Create the sketch for btm_rol
model.ConstrainedSketch(name='btm_rol_p', sheetSize=200.0)
s = model.sketches['btm_rol_p']
s.ArcByStartEndTangent(point1=(b_r, 0.0), point2=(-b_r, 0.0), vector=(1.0, 0.0))
# Create btm_rol
p=model.Part    (dimensionality=TWO_D_PLANAR, name='btm_rol', type=DISCRETE_RIGID_SURFACE)
p.BaseWire      (sketch=s)
p.Surface       (name='br_cnt'  , side2Edges=p.edges[:])
# Create reference point
rp=p.ReferencePoint(point=(0,0.0,0))
p.Set(name='btm_rp', referencePoints=(p.referencePoints[rp.id], ))


# Create the sketch for up_rol
model.ConstrainedSketch(name='up_rol_p', sheetSize=200.0)
s = model.sketches['up_rol_p']
s.ArcByCenterEnds(center=(0.0, b_r), direction=CLOCKWISE,point1=(b_r, b_r), point2=(0.0, 0.0))
# Create up_rol
p=model.Part    (dimensionality=TWO_D_PLANAR, name='up_rol', type=DISCRETE_RIGID_SURFACE)
p.BaseWire      (sketch=s)
p.Surface       (name='ur_cnt'  , side1Edges=p.edges[:])
# Create reference point
rp=p.ReferencePoint(point=(0,b_r,0))
p.Set(name='up_rp', referencePoints=(p.referencePoints[rp.id], ))

# Create materials
p1=model.parts['base_shell']
p2=model.parts['btm_rol']
p3=model.parts['up_rol']
create_material( 'matrix', matrix_pr,p1)
# Assembly
asmb.DatumCsysByDefault(CARTESIAN)
create_instance('base_shell')
create_instance('btm_rol')
create_instance('up_rol')
asmb.translate(instanceList=('btm_rol-1', ), 
    vector=(s_l/2-sout, -b_r, 0.0))
asmb.translate(instanceList=('up_rol-1', ), 
    vector=(0.0, s_h, 0.0))
ins1=asmb.instances['base_shell-1']
ins2=asmb.instances['up_rol-1']
ins3=asmb.instances['btm_rol-1']
asmb.Set(faces=ins1.faces[:], name='all')

# Create static steps
create_static_step('Initial', 'st_1', 0.5, 0.5)
create_static_step('st_1', 'st_2', 0.5, 0.5)

# # Create history output request
model.HistoryOutputRequest(createStepName='st_1', name='H-Output-1', region=ins2.sets['up_rp'], variables=('U2', 'RF2'))
model.HistoryOutputRequest(createStepName='st_1', name='H-Output-2', variables=('ALLSE',))
model.HistoryOutputRequest(createStepName='st_1', name='H-Output-3', variables=('ALLFD',))


# Partition and mesh
asmb.seedPartInstance(regions=(ins1, ins2, ins3), size=m_s)
asmb.seedEdgeBySize(constraint=FINER, edges=ins1.sets['eg_xsym2'].edges, size=ct_ms)
asmb.generateMesh(regions=(ins1, ins2, ins3))


# Interaction
model.ContactProperty('inp1')
# model.interactionProperties['inp1'].TangentialBehavior(formulation=FRICTIONLESS)
model.interactionProperties['inp1'].TangentialBehavior(formulation=PENALTY, fraction=0.005,table=((fc, ), ))
model.interactionProperties['inp1'].NormalBehavior(pressureOverclosure=HARD)

model.SurfaceToSurfaceContactStd( createStepName='Initial', 
     interactionProperty='inp1', main=ins2.surfaces['ur_cnt']
    , name='upper_roller', secondary=ins1.surfaces['up_cnt'], sliding=FINITE)
model.SurfaceToSurfaceContactStd( createStepName='Initial', 
     interactionProperty='inp1', main=ins3.surfaces['br_cnt']
    , name='bottom_roller', secondary=ins1.surfaces['bt_cnt'], sliding=FINITE)

model.ContactStd(createStepName='Initial', name='Int-3')
int3=model.interactions['Int-3']
int3.includedPairs.setValuesInStep(stepName='Initial', useAllstar=ON)
int3.contactPropertyAssignments.appendInStep(assignments=((GLOBAL, SELF, 'inp1'), ), stepName='Initial')





# Boundary conditions
model.DisplacementBC(createStepName='st_1', name='bc_btrol', region=ins3.sets['btm_rp'], u1=0.0, u2=0.0, ur3=0.0)


# Set nodes on symmetry line 
eg_xsym2_n = ins1.sets['eg_xsym2'].nodes


# Sort nodes based on y-coordinate and storing coordinates of nodes of 'eg_xsym2 ' set in list
sorted_nodes = sorted([n for n in eg_xsym2_n ], key=lambda n: n.coordinates[1])
eg_xsym2_nl=[]
for node in sorted_nodes:
    eg_xsym2_nl.append((node.coordinates,node.label))

# Create individual sets for each node
for i, node in enumerate(sorted_nodes[:]):
    asmb.Set(name='ns_' + str(i + 1), nodes=ins1.nodes.sequenceFromLabels([node.label]))
    model.DisplacementBC(createStepName='st_1', name='ns_bc_' +str(i+1), 
        region=asmb.sets['ns_' + str(i + 1)], u1=0, ur3=0)


##########################################################
# Main loop for simulation
##########################################################

jb_cnt, st_cnt, nd_cnt =0, 2, 0 # Counters for tracking job, step, and node numbers
max_p_matrix=0
g_c=g_c1
a=n_h
exit_all = False
g=0
nd_cnt += 1

disp=0
f_l, d_l, g_l, a_l = [0], [0], [0], [n_h]
max_p_l=[0] 
flg=-1
try:
    while g < g_c and disp < disp_lim:
    # while g < g_c and nd_cnt < 10:
    # for i in range (6) :
        jb_cnt += 1
        st_n = 'st_{}'.format(st_cnt)
        jb_n = 'jb_{}'.format(str(jb_cnt).zfill(3))
        st_o = 'st_{}'.format(st_cnt-1)
        st_oo = 'st_{}'.format(st_cnt-2)
        jb_o = 'jb_{}'.format(str(jb_cnt-1).zfill(3))
        nd_n = 'ns_bc_{}'.format(nd_cnt)
        disp = adpt_disp( disp )

        model.boundaryConditions[nd_n].deactivate(st_n)
        model.DisplacementBC(createStepName=st_o, name='BC-1', region=ins2.sets['up_rp'], u1=0.0, u2=-disp, ur3=0.0)
        
        if flg == -1 :
            model.setValues(restartIncrement=STEP_END, restartJob=jb_o, restartStep=st_o)
            job = mdb.Job ( model='Model-1', name=jb_n, numCpus=4, numDomains=4, resultsFormat=ODB )

        else:
            model.setValues(restartIncrement=STEP_END, restartJob=jb_i, restartStep=st_oo)
            job = mdb.Job(model='Model-1', name=jb_n, numCpus=4, numDomains=4, resultsFormat=ODB, type=RESTART)
            print('jb_i', jb_i)

        
        job.submit()
        job.waitForCompletion()
        odb = session.openOdb(jb_n + '.odb')

        da=abs (eg_xsym2_nl[nd_cnt][0][1]-eg_xsym2_nl[nd_cnt-1][0][1])


        g,rf2,ru2 =get_energy_release_rate(st_n, da)
        max_p_evoh = get_max_principal(st_n)
        if max_p_evoh > sig_c :
            exit_all = True
            break
        # export_field_images(jb_n, st_n)
        odb.close()
        f_l.append(rf2)
        d_l.append(ru2)
        a_l.append(a_l[-1])
        g_l.append(g)
        max_p_l.append(max_p_evoh)
        while g > g_c :

            jb_cnt += 1
            st_cnt += 1
            nd_cnt += 1

            st_n = 'st_{}'.format(st_cnt)
            jb_n = 'jb_{}'.format(str(jb_cnt).zfill(3))
            nd_n = 'ns_bc_{}'.format(nd_cnt)
            st_o = 'st_{}'.format(st_cnt-1)
            jb_o = 'jb_{}'.format(str(jb_cnt-1).zfill(3))

            create_static_step(st_o, st_n, 0.5, 0.5)


            model.boundaryConditions[nd_n].deactivate(st_n)


            model.setValues(restartIncrement=STEP_END, restartJob=jb_o, restartStep=st_o)
            job = mdb.Job(model='Model-1', name=jb_n, numCpus=4, numDomains=4, resultsFormat=ODB, type=RESTART)
            job.submit()
            job.waitForCompletion()
            odb = session.openOdb(jb_n + '.odb')

            da=m_s
            g_c=g_c1

            g,rf2,ru2 =get_energy_release_rate(st_n,da)
            max_p_evoh=get_max_principal(st_n)
            a=a_l[-1]+da    
            g_l.append(g)
            a_l.append(a_l[-1]+da) 
            f_l.append(rf2)
            d_l.append(ru2)
            max_p_l.append(max_p_evoh)
            if max_p_evoh > sig_c :
                exit_all = True
                break
            odb.close()
            if g < g_c :
                jb_i='jb_{}'.format(str(jb_cnt-1).zfill(3))
                jb_cnt += -1

                model.boundaryConditions[nd_n].reset(st_n)
                st_cnt += 1
                flg=1
                st_n = 'st_{}'.format(st_cnt)
                st_o = 'st_{}'.format(st_cnt-1)
                create_static_step(st_o, st_n, 0.5, 0.5)
except Exception as e:
      print("An error occurred: {}".format(str(e)))
        
##########################################################
# plot
##########################################################

# Setup: clear plots and define style
for plot_name in session.xyPlots.keys(): del session.xyPlots[plot_name]

font_tn = '-*-times new roman-medium-r-normal-*-*-240-*-*-p-*-*-*'
colors = {'black': '#000000', 'red': '#C60000', 'white': '#FFFFFF'}

# Create and plot data
xy_obj = session.XYData(name='Force-Displacement', data=list(zip(d_l, f_l)))
curve = session.Curve(xyData=xy_obj)
xy_plot = session.XYPlot(name='Force-Displacement Plot')
# Display the plot
vp = session.viewports[session.currentViewportName]
vp.setValues(displayedObject=xy_plot)

chart_n=session.charts.keys()[-1]
chart = session.charts[session.charts.keys()[-1]]
chart.setValues(curvesToPlot=(curve,), aspectRatio=1.0)
chart.gridArea.style.setValues(color=colors['white'])

# Style curve
session.curves['Force-Displacement'].lineStyle.setValues(color=colors['red'], thickness=0.5)



# Axis formatting
x_axis = chart.axes1[0]
y_axis = chart.axes2[0]
x_axis.axisData.setValues(useSystemTitle=False, title='Displacement (mm)')
x_axis.titleStyle.setValues(font=font_tn)
y_axis.axisData.setValues(useSystemTitle=False, title='Force (N)', scale=LINEAR)
y_axis.titleStyle.setValues(color=colors['black'], font=font_tn)

# chart legend
ch_la=session.charts[chart_n].legend.area
ch_la.setValues(inset=True)
ch_la.setValues(positionMethod=MANUAL)
ch_la.setValues(originOffset=(0.09, 0.86)) 
ch_la.border.setValues(show=True)
session.charts[chart_n].legend.textStyle.setValues(font=font_tn, color=colors['black'])
# delete_files()

# Write to CSV using built-in Python
with open('../'+model_name+'/force_displacement.csv', 'w') as f:
    f.write('Displacement,Force\n')
    for d, fval in zip(d_l, f_l):
        f.write('%s,%s\n' % (d, fval))
        
mdb.saveAs(pathName=model_name+'.cae')

