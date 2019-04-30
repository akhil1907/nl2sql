import os
import re

from .constants import Color
from .table import Table


class Database:

    def __init__(self):
        self.tables = []
        self.thesaurus_object = None

    def set_thesaurus(self, thesaurus):
        self.thesaurus_object = thesaurus

    def get_number_of_tables(self):
        return len(self.tables)

    def get_tables(self):
        return self.tables

    def get_column_with_this_name(self, name):
        for table in self.tables:
            for column in table.get_columns():
                if column.name == name:
                    return column

    def get_table_by_name(self, table_name):
        for table in self.tables:
            if table.name == table_name:
                return table

    def get_tables_into_dictionary(self):
        data = {}
        for table in self.tables:
            data[table.name] = []
            for column in table.get_columns():
                data[table.name].append(column.name)
        return data

    def get_primary_keys_by_table(self):
        data = {}
        for table in self.tables:
            data[table.name] = table.get_primary_keys()
        return data

    def get_foreign_keys_by_table(self):
        data = {}
        for table in self.tables:
            data[table.name] = table.get_foreign_keys()
        return data

    def get_primary_keys_of_table(self, table_name):
        for table in self.tables:
            if table.name == table_name:
                return table.get_primary_keys()

    def get_primary_key_names_of_table(self, table_name):
        for table in self.tables:
            if table.name == table_name:
                return table.get_primary_key_names()

    def get_foreign_keys_of_table(self, table_name):
        for table in self.tables:
            if table.name == table_name:
                return table.get_foreign_keys()

    def get_foreign_key_names_of_table(self, table_name):
        for table in self.tables:
            if table.name == table_name:
                return table.get_foreign_key_names()

    def add_table(self, table):
        self.tables.append(table)

    @staticmethod
    def _generate_path(path):
        cwd = os.path.dirname(__file__)
        filename = os.path.join(cwd, path)
        return filename

    def load(self, path):
        with open(self._generate_path(path)) as f:
            content = f.read()
            tables_string = [p.split(';')[0] for p in content.split('CREATE') if ';' in p]
            for table_string in tables_string:
                if 'TABLE' in table_string:
                    table = self.create_table(table_string)
                    self.add_table(table)
            alter_tables_string = [p.split(';')[0] for p in content.split('ALTER') if ';' in p]
            for alter_table_string in alter_tables_string:
                if 'TABLE' in alter_table_string:
                    self.alter_table(alter_table_string)

    def predict_type(self, string):
        if 'int' in string.lower():
            return 'int'
        elif 'char' in string.lower() or 'text' in string.lower():
            return 'string'
        elif 'date' in string.lower():
            return 'date'
        elif 'double' in string.lower():
            return 'double'
        else:
            return 'unknown'
    
    def get_column(self, column_name, line):
        column_type = self.predict_type(line)
        equivalences = [column_name.group(1).lower()]
        if self.thesaurus_object is not None:
            equivalences.append(self.thesaurus_object.get_synonyms_of_a_word(column_name.group(1)))
        
        return column_name.group(1), column_type, equivalences


    def create_table(self, table_string):
        lines = table_string.split("\n")
        table = Table()
        for line in lines:
            if 'TABLE' in line:
                table_name = re.search("`(\w+)`", line)
                table.name = table_name.group(1)
                table.equivalences = [table.name.lower()]
                if self.thesaurus_object is not None:
                    table.equivalences.append(self.thesaurus_object.get_synonyms_of_a_word(table.name))
            elif 'PRIMARY KEY' in line:
                primary_key_columns = re.finditer("`(\w+)`", line)
                for primary_key_column in primary_key_columns:
                    exists = False
                    for col in table.columns:
                        if col.name == primary_key_column.group(1):
                            exists = True
                    if not exists:
                        x,y,z = self.get_column(primary_key_column,line)
                        table.add_column(x,y,z)
                        print("--------Primary---------------- :::::::",x)
                    table.add_primary_key(primary_key_column.group(1))
            elif 'FOREIGN KEY' in line:
                # print("Foreign key in line")
                foreign_keys_list = re.findall("FOREIGN KEY \(`(\w+)`\) REFERENCES `(\w+)` \(`(\w+)`\)", line)
                for column, foreign_table, foreign_column in foreign_keys_list:
                    table.add_foreign_key(column, foreign_table, foreign_column)
            else:
                column_name = re.search("`(\w+)`", line)
                if column_name is not None:
                    x,y,z = self.get_column(column_name,line)
                    table.add_column(x,y,z)
        return table

    def alter_table(self, alter_string):
        lines = alter_string.replace('\n', ' ').split(';')
        for line in lines:
            if 'PRIMARY KEY' in line:
                table_name = re.search("TABLE `(\w+)`", line).group(1)
                table = self.get_table_by_name(table_name)
                primary_key_columns = re.findall("PRIMARY KEY \(`(\w+)`\)", line)
                for primary_key_column in primary_key_columns:
                    table.add_primary_key(primary_key_column)
            elif 'FOREIGN KEY' in line:
                print("Foreign key in line")
                table_name = re.search("TABLE `(\w+)`", line).group(1)
                table = self.get_table_by_name(table_name)
                foreign_keys_list = re.findall("FOREIGN KEY \(`(\w+)`\) REFERENCES `(\w+)` \(`(\w+)`\)", line)
                for column, foreign_table, foreign_column in foreign_keys_list:
                    table.add_foreign_key(column, foreign_table, foreign_column)


    def print_me(self):
        for table in self.tables:
            print('+-------------------------------------+')
            print("| %25s           |" % (table.name.upper()))
            print('+-------------------------------------+')
            for column in table.columns:
                # print(column.is_foreign())
                if column.is_primary():
                    print("| 🔑 %31s           |" % (Color.BOLD + column.name + ' (' + column.type + ')' + Color.END))
                elif column.is_foreign():
                    print("| #️⃣ %31s           |" % (Color.BOLD + column.name + ' (' + column.type + ')' + Color.END))
                else:
                    print("|   %23s           |" % (column.name + ' (' + column.type + ')'))
            print('+-------------------------------------+\n')
