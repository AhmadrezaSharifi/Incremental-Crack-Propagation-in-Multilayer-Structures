import os

model_name=  'fl_1'
new_dir = r'../'+model_name

# Change the current working directory
os.chdir(new_dir)

# merge the odb files into one
odb_files = sorted([i[:-4] for i in os.listdir(os.path.abspath('')) if i.endswith('.odb')])
print(odb_files)
os.system('abaqus restartjoin originalodb='+odb_files[0]+' restartodb='+odb_files[1]+' history copyoriginal')
restart_odb = 'Restart_'+odb_files[0]
for odb_file in odb_files[2:]:
    os.system('abaqus restartjoin originalodb='+restart_odb+' restartodb='+odb_file+' history')