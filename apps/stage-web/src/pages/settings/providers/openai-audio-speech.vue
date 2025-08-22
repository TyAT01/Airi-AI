<script setup lang="ts">
import type { SpeechProvider } from '@xsai-ext/shared-providers'
import type { RemovableRef } from '@vueuse/core'

import {
  ProviderAdvancedSettings,
  ProviderApiKeyInput,
  ProviderBaseUrlInput,
  ProviderBasicSettings,
  ProviderSettingsContainer,
  ProviderSettingsLayout,
  SpeechPlayground,
} from '@proj-airi/stage-ui/components'
import { useProvidersStore, useSpeechStore } from '@proj-airi/stage-ui/stores'
import { FieldRange } from '@proj-airi/ui'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const speechStore = useSpeechStore()
const providersStore = useProvidersStore()
const { providers } = storeToRefs(providersStore) as { providers: RemovableRef<Record<string, any>> }
const { t } = useI18n()
const router = useRouter()

const defaultVoiceSettings = {
  speed: 1.0,
}

// Get provider metadata
const providerId = 'openai-audio-speech'
const defaultModel = 'tts-1'
const providerMetadata = computed(() => providersStore.getProviderMetadata(providerId))

const speed = ref<number>(1.0)

// Use computed properties for settings
const apiKey = computed({
  get: () => providers.value[providerId]?.apiKey || '',
  set: (value) => {
    if (!providers.value[providerId])
      providers.value[providerId] = {}
    providers.value[providerId].apiKey = value
  },
})

const baseUrl = computed({
  get: () => providers.value[providerId]?.baseUrl || 'https://api.openai.com/v1/',
  set: (value) => {
    if (!providers.value[providerId])
      providers.value[providerId] = {}
    providers.value[providerId].baseUrl = value
  },
})

onMounted(() => {
  // Initialize provider if it doesn't exist
  if (!providers.value[providerId]) {
    providers.value[providerId] = {
      baseUrl: 'https://api.openai.com/v1/',
    }
  }

  // Initialize refs with current values
  apiKey.value = providers.value[providerId]?.apiKey || ''
  baseUrl.value = providers.value[providerId]?.baseUrl || 'https://api.openai.com/v1/'
})

// Watch settings and update the provider configuration
watch([apiKey, baseUrl], () => {
  providers.value[providerId] = {
    ...providers.value[providerId],
    apiKey: apiKey.value,
    baseUrl: baseUrl.value || 'https://api.openai.com/v1/',
  }
})

// Check if API key is configured
const apiKeyConfigured = computed(() => !!providers.value[providerId]?.apiKey)

const availableVoices = computed(() => {
  return speechStore.availableVoices[providerId] || []
})

// Generate speech with ElevenLabs-specific parameters
async function handleGenerateSpeech(input: string, voiceId: string, _useSSML: boolean) {
  const provider = await providersStore.getProviderInstance<SpeechProvider<string>>(providerId)
  if (!provider) {
    throw new Error('Failed to initialize speech provider')
  }

  // Get provider configuration
  const providerConfig = providersStore.getProviderConfig(providerId)

  // Get model from configuration or use default
  const model = providerConfig.model as string | undefined || defaultModel

  // ElevenLabs doesn't need SSML conversion, but if SSML is provided, use it directly
  return await speechStore.speech(
    provider,
    model,
    input,
    voiceId,
    {
      ...providerConfig,
      ...defaultVoiceSettings,
    },
  )
}

function handleResetSettings() {
  providers.value[providerId] = {
    baseUrl: 'https://api.openai.com/v1/',
  }
}

watch(speed, async () => {
  const providerConfig = providersStore.getProviderConfig(providerId)
  providerConfig.speed = speed.value
})
</script>

<template>
  <ProviderSettingsLayout
    :provider-name="providerMetadata?.localizedName || 'OpenAI'"
    :provider-icon="providerMetadata?.icon"
    :on-back="() => router.back()"
  >
    <ProviderSettingsContainer>
      <ProviderBasicSettings
        :title="t('settings.pages.providers.common.section.basic.title')"
        :description="t('settings.pages.providers.common.section.basic.description')"
        :on-reset="handleResetSettings"
      >
        <ProviderApiKeyInput
          v-model="apiKey"
          :provider-name="providerMetadata?.localizedName || 'OpenAI'"
          placeholder="sk-..."
        />
      </ProviderBasicSettings>

      <ProviderAdvancedSettings :title="t('settings.pages.providers.common.section.advanced.title')">
        <ProviderBaseUrlInput
          v-model="baseUrl"
          placeholder="https://api.openai.com/v1/"
        />
      </ProviderAdvancedSettings>
    </ProviderSettingsContainer>
    <!-- Voice settings specific to ElevenLabs -->
    <template #voice-settings>
      <!-- Speed control - common to most providers -->
      <FieldRange
        v-model="speed"
        :label="t('settings.pages.providers.provider.common.fields.field.speed.label')"
        :description="t('settings.pages.providers.provider.common.fields.field.speed.description')"
        :min="0.5"
        :max="2.0" :step="0.01"
      />
    </template>

    <template #playground>
      <SpeechPlayground
        :available-voices="availableVoices"
        :generate-speech="handleGenerateSpeech"
        :api-key-configured="apiKeyConfigured"
        default-text="Hello! This is a test of the OpenAI Speech."
      />
    </template>
  </ProviderSettingsLayout>
</template>

<route lang="yaml">
  meta:
    layout: settings
    stageTransition:
      name: slide
  </route>
