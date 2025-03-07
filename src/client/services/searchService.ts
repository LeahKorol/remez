
import api from './api';
import { toast } from 'sonner';

export interface SavedSearch {
  id: string;
  name: string;
  text: string;
  date: string;
  medications: string[];
  sideEffect: string;
  medication1: string;
  medication2: string;
  result: {
    likelihood: string;
    data: { name: string; value: number }[];
  };
}

export interface SearchInput {
  medication1: string;
  medication2: string;
  sideEffect: string;
  result: {
    likelihood: string;
    data: { name: string; value: number }[];
  };
}

export const searchService = {
  // Get all saved searches for a user
  async getSavedSearches(uid: string): Promise<SavedSearch[]> {
    try {
      const { data } = await api.get(`/users/${uid}/queries`);
      
      // Transform the backend data to match our frontend model
      return data.map((query: any) => ({
        id: query.id,
        name: query.name,
        text: query.text,
        date: new Date(query.created_at || Date.now()).toISOString().split('T')[0],
        medications: query.text.split(' + '),
        sideEffect: query.name,
        medication1: query.text.split(' + ')[0],
        medication2: query.text.split(' + ')[1],
        result: JSON.parse(query.result || '{"likelihood":"moderate","data":[]}')
      }));
    } catch (error) {
      console.error('Error fetching saved searches:', error);
      toast.error('Failed to load saved searches');
      return [];
    }
  },

  // Save a new search
  async saveSearch(uid: string, searchData: SearchInput): Promise<SavedSearch | null> {
    try {
      const payload = {
        name: searchData.sideEffect,
        text: `${searchData.medication1} + ${searchData.medication2}`,
        result: JSON.stringify(searchData.result)
      };
      
      const { data } = await api.post(`/users/${uid}/queries`, payload);
      
      return {
        id: data.id,
        name: data.name,
        text: data.text,
        date: new Date(data.created_at || Date.now()).toISOString().split('T')[0],
        medications: data.text.split(' + '),
        sideEffect: data.name,
        medication1: searchData.medication1,
        medication2: searchData.medication2,
        result: searchData.result
      };
    } catch (error) {
      console.error('Error saving search:', error);
      toast.error('Failed to save search');
      return null;
    }
  },

  // Delete a saved search
  async deleteSearch(uid: string, searchId: string): Promise<boolean> {
    try {
      await api.delete(`/users/${uid}/queries/${searchId}`);
      return true;
    } catch (error) {
      console.error('Error deleting search:', error);
      toast.error('Failed to delete search');
      return false;
    }
  }
};
