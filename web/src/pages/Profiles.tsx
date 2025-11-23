import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { Profile, ProfileMapping, ValidationRules } from '../types/api';

export function Profiles() {
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  // Profile creation form state
  const [profileName, setProfileName] = useState('');
  const [fileType, setFileType] = useState('XML');
  const [description, setDescription] = useState('');
  const [mappings, setMappings] = useState<ProfileMapping[]>([{
    source_path: '',
    target_path: '',
    data_type: 'string',
    required: false,
    default_value: '',
    transform: ''
  }]);
  const [requiredFields, setRequiredFields] = useState<string[]>([]);
  const [newRequiredField, setNewRequiredField] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);

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

  const createProfileMutation = useMutation({
    mutationFn: (profile: Profile) => apiClient.createProfile(profile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      resetForm();
      setIsCreating(false);
      setCreateError(null);
    },
    onError: (error: any) => {
      setCreateError(error.response?.data?.detail || error.message || 'Failed to create profile');
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

  // Profile creation form helpers
  const resetForm = () => {
    setProfileName('');
    setFileType('XML');
    setDescription('');
    setMappings([{
      source_path: '',
      target_path: '',
      data_type: 'string',
      required: false,
      default_value: '',
      transform: ''
    }]);
    setRequiredFields([]);
    setNewRequiredField('');
    setCreateError(null);
  };

  const addMapping = () => {
    setMappings([...mappings, {
      source_path: '',
      target_path: '',
      data_type: 'string',
      required: false,
      default_value: '',
      transform: ''
    }]);
  };

  const removeMapping = (index: number) => {
    setMappings(mappings.filter((_, i) => i !== index));
  };

  const updateMapping = (index: number, field: keyof ProfileMapping, value: any) => {
    const updated = [...mappings];
    updated[index] = { ...updated[index], [field]: value };
    setMappings(updated);
  };

  const addRequiredField = () => {
    if (newRequiredField.trim() && !requiredFields.includes(newRequiredField.trim())) {
      setRequiredFields([...requiredFields, newRequiredField.trim()]);
      setNewRequiredField('');
    }
  };

  const removeRequiredField = (field: string) => {
    setRequiredFields(requiredFields.filter(f => f !== field));
  };

  const handleCreateProfile = () => {
    setCreateError(null);

    // Validation
    if (!profileName.trim()) {
      setCreateError('Profile name is required');
      return;
    }

    if (mappings.length === 0 || mappings.every(m => !m.source_path || !m.target_path)) {
      setCreateError('At least one complete mapping is required');
      return;
    }

    // Filter out incomplete mappings
    const completeMappings = mappings.filter(m => m.source_path && m.target_path);

    const profile: Profile = {
      profile_name: profileName.trim(),
      file_type: fileType,
      description: description.trim(),
      mappings: completeMappings,
      validation_rules: {
        required_fields: requiredFields,
      },
      transformations: {}
    };

    createProfileMutation.mutate(profile);
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

      {/* Create Profile Modal */}
      {isCreating && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 my-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Create New Profile</h2>
              <button
                onClick={() => {
                  resetForm();
                  setIsCreating(false);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Error Message */}
            {createError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                <p className="text-red-800 text-sm">{createError}</p>
              </div>
            )}

            <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Profile Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={profileName}
                    onChange={(e) => setProfileName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., my_custom_format"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    File Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={fileType}
                    onChange={(e) => setFileType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="XML">XML</option>
                    <option value="JSON">JSON</option>
                    <option value="CSV">CSV</option>
                    <option value="PDF">PDF</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Describe this profile and when to use it..."
                />
              </div>

              {/* Mappings */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Field Mappings <span className="text-red-500">*</span>
                  </label>
                  <button
                    onClick={addMapping}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    + Add Mapping
                  </button>
                </div>

                <div className="space-y-3">
                  {mappings.map((mapping, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Source Path</label>
                          <input
                            type="text"
                            value={mapping.source_path}
                            onChange={(e) => updateMapping(index, 'source_path', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                            placeholder="/root/field or $.data.field"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Target Path</label>
                          <input
                            type="text"
                            value={mapping.target_path}
                            onChange={(e) => updateMapping(index, 'target_path', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                            placeholder="canonical_field_name"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-4 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Data Type</label>
                          <select
                            value={mapping.data_type}
                            onChange={(e) => updateMapping(index, 'data_type', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                          >
                            <option value="string">String</option>
                            <option value="integer">Integer</option>
                            <option value="float">Float</option>
                            <option value="boolean">Boolean</option>
                            <option value="date">Date</option>
                            <option value="array">Array</option>
                          </select>
                        </div>
                        <div className="flex items-end">
                          <label className="flex items-center text-sm text-gray-700">
                            <input
                              type="checkbox"
                              checked={mapping.required}
                              onChange={(e) => updateMapping(index, 'required', e.target.checked)}
                              className="mr-2 rounded"
                            />
                            Required
                          </label>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Default Value</label>
                          <input
                            type="text"
                            value={mapping.default_value || ''}
                            onChange={(e) => updateMapping(index, 'default_value', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                            placeholder="Optional"
                          />
                        </div>
                        <div className="flex items-end">
                          <button
                            onClick={() => removeMapping(index)}
                            disabled={mappings.length === 1}
                            className="w-full px-2 py-1 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Validation Rules */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Required Fields
                </label>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newRequiredField}
                      onChange={(e) => setNewRequiredField(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addRequiredField()}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter field name and press Enter"
                    />
                    <button
                      onClick={addRequiredField}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Add
                    </button>
                  </div>
                  {requiredFields.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {requiredFields.map((field) => (
                        <div
                          key={field}
                          className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                        >
                          <span>{field}</span>
                          <button
                            onClick={() => removeRequiredField(field)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
              <button
                onClick={() => {
                  resetForm();
                  setIsCreating(false);
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateProfile}
                disabled={createProfileMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createProfileMutation.isPending ? 'Creating...' : 'Create Profile'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
