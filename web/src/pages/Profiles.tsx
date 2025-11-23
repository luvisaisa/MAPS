import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { Profile } from '../types/api';

export function Profiles() {
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  const { data: profiles = [], isLoading, error } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => apiClient.getProfiles(),
  });

  const deleteProfileMutation = useMutation({
    mutationFn: (profileName: string) => apiClient.deleteProfile(profileName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      setSelectedProfile(null);
    },
  });

  const filteredProfiles = profiles.filter(profile =>
    profile.profile_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (profile.description?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  const handleProfileClick = (profile: Profile) => {
    setSelectedProfile(profile);
  };

  const handleDeleteProfile = (profileName: string) => {
    if (window.confirm(`Are you sure you want to delete profile "${profileName}"?`)) {
      deleteProfileMutation.mutate(profileName);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading profiles...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Profiles</h3>
          <p className="text-red-600">{(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Profiles</h1>
        <button
          onClick={() => setIsCreating(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Create New Profile
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search profiles..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile List */}
        <div className="lg:col-span-1 space-y-4">
          {filteredProfiles.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {searchTerm ? 'No profiles found' : 'No profiles available'}
            </div>
          ) : (
            filteredProfiles.map((profile) => (
              <div
                key={profile.profile_name}
                onClick={() => handleProfileClick(profile)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                  selectedProfile?.profile_name === profile.profile_name
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <h3 className="font-semibold text-gray-900">{profile.profile_name}</h3>
                {profile.description && (
                  <p className="text-sm text-gray-600 mt-1">{profile.description}</p>
                )}
                <div className="mt-2 text-xs text-gray-500">
                  {(profile.mappings || []).length} mappings
                </div>
              </div>
            ))
          )}
        </div>

        {/* Profile Details */}
        <div className="lg:col-span-2">
          {selectedProfile ? (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedProfile.profile_name}</h2>
                  {selectedProfile.description && (
                    <p className="text-gray-600 mt-2">{selectedProfile.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDeleteProfile(selectedProfile.profile_name)}
                    className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Mappings */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Mappings</h3>
                <div className="space-y-2">
                  {(selectedProfile.mappings || []).map((mapping, index) => (
                    <div key={index} className="flex items-center gap-4 p-3 bg-gray-50 rounded">
                      <span className="font-medium text-gray-700 min-w-[200px]">{mapping.source_path}</span>
                      <span className="text-gray-600">{mapping.target_path}</span>
                      <span className="text-xs text-gray-500">({mapping.data_type})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center h-64">
              <p className="text-gray-500">Select a profile to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Profile Modal (placeholder) */}
      {isCreating && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create New Profile</h2>
            <p className="text-gray-600 mb-4">Profile creation form coming soon...</p>
            <button
              onClick={() => setIsCreating(false)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
