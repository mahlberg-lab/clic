# -*- coding: utf-8 -*-
import copy
import pandas as pd


def facets_to_df(facets):
    '''
    Converts the facets into a dataframe that can be manipulated
    more easily.
    '''
    def select_third_value(value):
        '''
        Facets come in the following format:
        [(u'a', (38, 879, 84372)),
         (u'all', (1067, 879, 15104)),

        This function returns the third values, respectively 84372 and 15104
        in the example above.
        '''
        return value[2]

    dataframe = pd.DataFrame(facets, columns =['Type', 'Raw facet'])
    dataframe.index += 1

    dataframe['Count'] = dataframe['Raw facet'].apply(select_third_value)
    total = dataframe.Count.sum()
    dataframe['Percentage'] = dataframe.Count / total * 100
    dataframe['Percentage'] = dataframe['Percentage'].round(decimals=2)
    dataframe.sort_values(by='Count', ascending=False, inplace=True)
    dataframe['Empty'] = ''
    return dataframe


def wordlist_to_json(self):
    '''
    Returns a json string that is 
    adapted to the CLiC API.
    '''
    # do not work on the original
    wordlist = copy.deepcopy(self.wordlist)
    del wordlist['Raw facet']
    wordlist = wordlist[['Empty', 'Type', 'Count', 'Percentage']]
    return wordlist.to_json(orient='values')
