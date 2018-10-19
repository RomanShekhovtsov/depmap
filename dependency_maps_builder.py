
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np
import os


# In[3]:


def load_Java_API_dependencies(file_name, sheet_name):
    return pd.read_excel(file_name,sheet_name=sheet_name, skiprows=2, usecols='B:WW',index_col=0,header=1 )

df_java_api = load_Java_API_dependencies('server-side.xlsm', 'Зависимости.JavaAPI')


# In[4]:


def replace_multi(string, replace_list, replace_string=''):
    for elem in replace_list :
        if elem in string :
            string = string.replace(elem, replace_string)    
    return  string


# In[311]:


# class Dependency:
    
#     def __init__(self, dep_name, dep_type):
#         self.name = dep_name
#         self.type = dep_type
        
#     def __str__(self):
#         return 'name: ' + self.name + '; type: ' + self.type


# In[5]:


class Metadata:
    
    def __init__(self, file_name):
        self.meta = pd.read_excel(file_name, encoding='1251')

    def get(self, id_column, id_value, data_column):
        
        values = self.meta.loc[self.meta[id_column]==id_value][data_column].values
        if values.shape[0]>0:
            value = values[0]
            if value != value:  # NaN
                value = ''                
        else:
            value = ''
            
        return value

    def get_name(self, id_column_name, id_value):
        name = self.get(id_column_name, id_value, 'name')
        if name == '':
            print('for "{}"={} not found "name" in {}'.format(id_column_name, id_value, metadata_file))
        return name
    
#     def get_by_service_name(self, id_value, data_columns):
#         return self.get('service name', id_value, data_columns)

#     def get_by_client_lib(self, id_value, data_columns):
#         return self.get('client-lib name', id_value, data_columns)

#     def get_by_server_side(self, id_value, data_columns):
#         return self.get('server-side name', id_value, data_columns)
    
metadata_file = 'metadata.xlsx'    
meta = Metadata(metadata_file)    
meta.get( 'client-lib name', 'SSD', 'link')
meta.get( 'server-side name', 'Технологическое ядро', 'link')
meta.get( 'server-side name', 'Сессионные данные', ['client-lib name'])


# In[6]:


START_SUBSYSTEMS_COL = 3

def get_java_api_subsystems(df):
    subsystems = {}
    for i in range(START_SUBSYSTEMS_COL, len(df.columns)):
        column = df.columns[i]
        if not column.startswith('Unnamed:'):
            subsystem_name = column
            subsystems[subsystem_name] = i
    return subsystems

subsystems = get_java_api_subsystems(df_java_api)


# In[7]:


def get_java_api_deps_list(df, subsystems):
    dep_list = {}

    keys = list(subsystems.keys())

    for i in range(len(keys)):

        key = keys[i]

        #calc subsystem columns
        start = subsystems[key]    
        if i < len(keys) - 1:
            end = subsystems[keys[i + 1]]
        else:
            end = df.shape[1]  # last column

        subsystem_columns = df.iloc[:,start:end]
        subsystem_deps = {}

        # now go through dependencies
        for j in range(len(keys)):
            dep_key = keys[j]

            # calc dependencies rows        
            dep_start = subsystems[dep_key] - 1 #rows shifted by -1
            if j < len(keys) - 1:
                dep_end = subsystems[keys[j + 1]] - 1
            else:
                dep_end = df.shape[0]  # last row

            dep_rows = subsystem_columns.iloc[dep_start:dep_end]
            calls_count = np.sum(np.sum(dep_rows))

            if  calls_count > 0:
                dep_name = meta.get_name('server-side name', dep_key)
                subsystem_deps[dep_name] = ['- серверная часть']                
        
        name = meta.get_name('server-side name', key)
        dep_list[name] = subsystem_deps
        
    return dep_list


# In[8]:


def load_client_libs_dependenciec(file_name):
    df = pd.read_excel(file_name, encoding='1251', index_col=0)
    #df.head()
    # columns = ['Service']
    # columns.extend(list(df.iloc[:,0]))
    # columns.append('Comment')
    # print(columns)
    # df.columns= columns
    # df.head()
    df.columns = df.columns.map(lambda s: s.split('(')[0].strip())
    return df
    #df.head(30)

df_client_libs = load_client_libs_dependenciec('client-libs.xlsx')
#df_client_libs.head()


# In[9]:


def get_client_libs_dependencies(df, deps):    
    
    df.fillna('X', inplace=True)
    
    for row in range(df.shape[1] - 1):
        
        name = df.columns[row + 1]
        if name.startswith('Unnamed:'): # comments column & etc.
            continue
            
        name = meta.get_name('client-lib name', name)        
        dep_dic = {}
        
        for col in range(1, df.shape[1]-1):
            
            cell_value = df.iloc[row, col]
            
            if cell_value not in ('X', 'Х'):
                
                dep_name = df.columns[col]
                dep_name = meta.get_name('client-lib name', dep_name)
        
                if name not in deps.keys():
                    deps[name] = {}

                if dep_name not in deps[name].keys():
                    deps[name][dep_name] = []

                deps[name][dep_name].append('- клиентский модуль')
            
    return deps

dependencies = get_java_api_deps_list(df_java_api, subsystems)
get_client_libs_dependencies(df_client_libs, dependencies)
#dependencies #['Прикладной мониторинг']


# In[386]:


#meta.meta['name']


# In[135]:


#metadata.loc[metadata['service name']=='Справочники'][['client-lib name','number']]
#get_service_metadata(metadata, 'service name', 'Справочники', ['client-lib name','number'])


# In[22]:


SERVICE_LINK='link'
LINE_BREAK='&lt;br&gt;'

HEADER_HEIGHT = 90
SERVICE_X = 100  # service shape left
SERVICE_Y = 140  # service shape top
SHAPE_WIDTH = 300   # any shape width
SHAPE_HEIGHT = 110  # any shape width
X_MARGIN = 200 
Y_MARGIN = 50

DEP_X = SERVICE_X + SHAPE_WIDTH + X_MARGIN

def id_generator():    
    id_ = 4  # dependency ids starts from 4
    while True:
        yield str(id_)
        id_ += 1
get_id = id_generator()

def generate_dependencies_maps(template_file_name,
                               dependencies, 
                               meta):

    template = open(template_file_name,'r', encoding='utf-8').read()
    schema = template

    diagrams_folder = 'diagrams'
    if not os.path.exists(diagrams_folder):
        os.makedirs(diagrams_folder)

    for name in dependencies.keys():  # server_side_deps.keys():
        file_name = replace_multi(name, [':','\\','/'])
        with open(diagrams_folder + '\\' + file_name + '.xml','w', encoding='utf-8') as f:

            link = str(meta.get('name', name, SERVICE_LINK))
            if link != '':
                link = 'link="' + link + '"'
            #print(name, link)

            schema = template
            schema = schema.replace('$$HEADER$$', 'Карта зависимостей \'' + name + '\'')
            schema = schema.replace('$$SERVICE$$', name)
            schema = schema.replace('$$SERVICE_LINK$$', link)

            splitted_schema = schema.split('$$DEP_BLOCK$$')
            schema = splitted_schema[0]
            dep_block = splitted_schema[1]
            dep_number = 0

            dep_figures = generate_dependencies(                
                    dependencies[name],
                    dep_block)

            schema += dep_figures
            schema += splitted_schema[2]             
            f.write(schema)
            print('file "{}" created in "{}" folder'.format(file_name, diagrams_folder))


def generate_dependencies(deps,
                          template):    
    
    schema = ''
    dep_number = 0
    
    for dep_name in deps.keys():
        dep_y = SERVICE_Y + dep_number * (SHAPE_HEIGHT + Y_MARGIN)                
        
        dep_types = 'Что зависит:' + LINE_BREAK + LINE_BREAK.join(deps[dep_name])
 
        link = str(meta.get('name', dep_name, SERVICE_LINK))
        if link != '':
            link = 'link="' + link + '"'
        
        dep_block = template.replace('$$DEPENDENCY$$', dep_name)
        dep_block = dep_block.replace('$$DEP_LINK$$', link)
        dep_block = dep_block.replace('$$DEP_X$$', str(DEP_X))
        dep_block = dep_block.replace('$$DEP_Y$$', str(dep_y))

        dep_block = dep_block.replace('$$DEP_ID$$', next(get_id))
        dep_block = dep_block.replace('$$ARROW_ID$$', next(get_id))
        dep_block = dep_block.replace('$$DEP_TYPES_ID$$', next(get_id))

        dep_block = dep_block.replace('$$DEP_TYPES$$', dep_types)
        dep_block = dep_block.replace('$$DEP_TYPES_X$$', str(DEP_X+120))
        dep_block = dep_block.replace('$$DEP_TYPES_Y$$', str(dep_y+SHAPE_HEIGHT - 20))

        schema += dep_block
        dep_number += 1

    return schema
            
    # '$$SERVICE$$'
    # '$$SERVICE_LINK$$'
    # '$$DEPENDENCY$$'
    
    # '$$DEP_LINK$$'
    # '$$DEP_X$$'
    # '$$DEP_Y$$'
    # '$$DEP_ID$$'
    # '$$DEP_START$$'
    # '$$DEP_END$$'
    
    # '$$DEP_TYPES_ID$$'
    # '$$DEP_TYPES$$'de
    # '$$DEP_TYPES_X$$'
    # '$$DEP_TYPES_Y$$'
    
    # 'Java API&lt;br&gt;client jar&lt;br&gt;''

    #"/pages/viewpage.action?pageId=604506616"
generate_dependencies_maps('template.xml', dependencies, meta)


# In[ ]:


dependencies


# In[19]:


#str(meta.get('server-side name', 'Управление параметрами', 'client-lib name'))
meta.get('name', 'Авторизация', SERVICE_LINK)

