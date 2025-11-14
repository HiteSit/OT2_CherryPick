import { useEffect, useMemo, useState } from 'react'
import {
  Accordion,
  ActionIcon,
  Button,
  Grid,
  Loader,
  NumberInput,
  Paper,
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
  Title,
  Tooltip,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconRefresh } from '@tabler/icons-react'
import * as TOML from '@ltd/j-toml'
import {
  useAddWorkingPlateEntry,
  useDeleteWorkingPlateEntry,
  useLabwareQuery,
  useMoveWorkingPlateEntry,
  usePatchSetting,
  useRawSettingsQuery,
  useReplaceSettings,
  useSettingsQuery,
} from '../api/hooks'
import type { LabwareEntry } from '../api/types'
import { SectionCard } from './SectionCard'
import { WorkingPlateTable } from './WorkingPlateTable'

const tipReuseOptions = [
  { label: 'Always', value: 'always' },
  { label: 'Per Source', value: 'per_source' },
  { label: 'Never', value: 'never' },
]

const modeOptions = [
  { label: 'Multi Channel', value: 'multi' },
  { label: 'Multi X1', value: 'multi_X1' },
  { label: 'Single X1', value: 'single_X1' },
]

const mixingLocationOptions = [
  { value: 'destination', label: 'Destination' },
  { value: 'source', label: 'Source' },
  { value: 'none', label: 'None' },
]

const sourceRemixOptions = [
  { value: 'once', label: 'Once' },
  { value: 'always', label: 'Always' },
]

function useLabwareOptions(): { options: LabwareEntry[]; isLoading: boolean } {
  const { data, isLoading } = useLabwareQuery()
  return { options: data?.labware ?? [], isLoading }
}

export function SettingsEditor() {
  const { data, isLoading } = useSettingsQuery()
  const rawQuery = useRawSettingsQuery()
  const { options: labwareOptions } = useLabwareOptions()
  const patchMutation = usePatchSetting()
  const replaceMutation = useReplaceSettings()
  const addWorkingPlateMutation = useAddWorkingPlateEntry()
  const deleteWorkingPlateMutation = useDeleteWorkingPlateEntry()
  const moveWorkingPlateMutation = useMoveWorkingPlateEntry()
  const [rawContent, setRawContent] = useState('')

  useEffect(() => {
    if (rawQuery.data) {
      setRawContent(rawQuery.data)
    }
  }, [rawQuery.data])

  const workingPlate = useMemo(() => data?.settings.working_plate ?? [], [data])

  const handlePatch = (path: string, value: unknown) => {
    patchMutation.mutate(
      { path, value },
      {
        onSuccess: () => notifications.show({ color: 'teal', title: 'Updated', message: `${path} saved.` }),
        onError: (error) => notifications.show({ color: 'red', title: 'Error', message: String(error) }),
      },
    )
  }

  const handleWorkingPlateUpdate = (
    index: number,
    field: keyof (typeof workingPlate)[number],
    value: string | number | boolean | null,
  ) => {
    handlePatch(`settings.working_plate[${index}].${field.toString()}`, value)
  }

  const handleRawSave = () => {
    try {
      const parsed = TOML.parse(rawContent) as Record<string, unknown>
      replaceMutation.mutate(parsed, {
        onSuccess: () => notifications.show({ color: 'teal', title: 'settings.toml updated', message: 'All changes saved.' }),
        onError: (error) => notifications.show({ color: 'red', title: 'Error updating settings', message: String(error) }),
      })
    } catch (error) {
      notifications.show({
        color: 'red',
        title: 'Invalid TOML',
        message: error instanceof Error ? error.message : 'Unable to parse TOML content.',
      })
    }
  }

  const handleAddWorkingPlate = () => {
    const defaultLabware = labwareOptions[0]?.labware_id
    addWorkingPlateMutation.mutate(
      {
        type: 'source',
        labware_id: defaultLabware,
        position_rack: '1',
        connection: 'Pipette_8',
      },
      {
        onSuccess: () => notifications.show({ color: 'teal', title: 'Working plate added', message: 'New entry appended.' }),
        onError: (error: unknown) =>
          notifications.show({ color: 'red', title: 'Unable to add entry', message: String(error) }),
      },
    )
  }

  const handleRemoveWorkingPlate = (index: number) => {
    deleteWorkingPlateMutation.mutate(index, {
      onSuccess: () => notifications.show({ color: 'teal', title: 'Removed', message: 'Working plate entry deleted.' }),
      onError: (error: unknown) =>
        notifications.show({ color: 'red', title: 'Unable to remove entry', message: String(error) }),
    })
  }

  const handleMoveWorkingPlate = (index: number, direction: 'up' | 'down') => {
    const target = direction === 'up' ? index - 1 : index + 1
    moveWorkingPlateMutation.mutate(
      { index, target },
      {
        onError: (error: unknown) =>
          notifications.show({ color: 'red', title: 'Unable to move entry', message: String(error) }),
      },
    )
  }

  if (isLoading || !data) {
    return (
      <Stack align="center" py="xl">
        <Loader />
        <Text c="dimmed">Loading settings...</Text>
      </Stack>
    )
  }

  const { general, liquid_handling: lh } = data.settings

  return (
    <Stack gap="lg">
      <SectionCard title="General Settings">
        <Grid>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Select
              label="Tip reuse"
              data={tipReuseOptions}
              value={general.tip_reuse}
              onChange={(value) => value && handlePatch('settings.general.tip_reuse', value)}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Select
              label="Mode"
              data={modeOptions}
              value={general.mode}
              onChange={(value) => value && handlePatch('settings.general.mode', value)}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <NumberInput
              label="Head speed (mm/min)"
              value={general.head_speed.speed}
              min={50}
              max={600}
              step={10}
              onChange={(value) => value !== '' && handlePatch('settings.general.head_speed.speed', value)}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Textarea
              label="Starting tip well"
              autosize
              minRows={1}
              value={general.starting_tip_well}
              onChange={(event) => handlePatch('settings.general.starting_tip_well', event.currentTarget.value)}
            />
          </Grid.Col>
        </Grid>
      </SectionCard>

      <SectionCard title="Pre-aspirate Contact">
        <Grid>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Switch
              label="Enabled"
              checked={lh.pre_aspirate_contact.enabled}
              onChange={(event) => handlePatch('settings.liquid_handling.pre_aspirate_contact.enabled', event.currentTarget.checked)}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <NumberInput
              label="Position offset (%)"
              value={lh.pre_aspirate_contact.position_offset_percent}
              min={0}
              max={100}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.pre_aspirate_contact.position_offset_percent', value)
              }
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <NumberInput
              label="Aspirate volume (µL)"
              value={lh.pre_aspirate_contact.aspirate_volume}
              min={0}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.pre_aspirate_contact.aspirate_volume', value)
              }
            />
          </Grid.Col>
        </Grid>
      </SectionCard>

      <SectionCard title="Post-aspirate Wick">
        <Grid>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Switch
              label="Enabled"
              checked={lh.post_aspirate_wick.enabled}
              onChange={(event) => handlePatch('settings.liquid_handling.post_aspirate_wick.enabled', event.currentTarget.checked)}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <NumberInput
              label="Radius"
              value={lh.post_aspirate_wick.radius}
              min={0}
              step={0.1}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.post_aspirate_wick.radius', Number(value))
              }
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <NumberInput
              label="Vertical offset (mm)"
              value={lh.post_aspirate_wick.v_offset_mm}
              step={0.1}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.post_aspirate_wick.v_offset_mm', Number(value))
              }
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <NumberInput
              label="Speed"
              value={lh.post_aspirate_wick.speed}
              min={1}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.post_aspirate_wick.speed', Number(value))
              }
            />
          </Grid.Col>
        </Grid>
      </SectionCard>

      <SectionCard title="Delays & Push-out">
        <Grid>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <NumberInput
              label="Post-aspirate delay (s)"
              value={lh.delays.post_aspirate}
              min={0}
              max={10}
              step={0.5}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.delays.post_aspirate', Number(value))
              }
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Switch
              label="Push-out enabled"
              checked={lh.push_out.enabled}
              onChange={(event) => handlePatch('settings.liquid_handling.push_out.enabled', event.currentTarget.checked)}
            />
            <NumberInput
              mt="sm"
              label="Push-out volume (µL)"
              value={lh.push_out.volume_ul}
              min={0}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.push_out.volume_ul', Number(value))
              }
            />
          </Grid.Col>
        </Grid>
      </SectionCard>

      <SectionCard title="Mixing">
        <Grid>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Select
              label="Location"
              data={mixingLocationOptions}
              value={lh.mixing.location}
              onChange={(value) => value && handlePatch('settings.liquid_handling.mixing.location', value)}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <NumberInput
              label="Repetitions"
              min={0}
              max={20}
              value={lh.mixing.repetitions}
              onChange={(value) =>
                value !== '' && handlePatch('settings.liquid_handling.mixing.repetitions', Number(value))
              }
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Select
              label="Source remixing"
              data={sourceRemixOptions}
              value={lh.mixing.source_remixing}
              onChange={(value) => value && handlePatch('settings.liquid_handling.mixing.source_remixing', value)}
            />
          </Grid.Col>
        </Grid>
      </SectionCard>

      <SectionCard
        title="Deck Layout"
        description={
          <Grid align="center">
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Text c="dimmed">Assign each working plate to a labware definition from your catalog.</Text>
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 4 }} style={{ textAlign: 'right' }}>
              <Button
                size="xs"
                onClick={handleAddWorkingPlate}
                loading={addWorkingPlateMutation.isPending}
                disabled={!labwareOptions.length}
              >
                Add labware
              </Button>
            </Grid.Col>
          </Grid>
        }
      >
        <WorkingPlateTable
          entries={workingPlate}
          labware={labwareOptions}
          onUpdate={handleWorkingPlateUpdate}
          onRemove={(index) => handleRemoveWorkingPlate(index)}
          onMove={handleMoveWorkingPlate}
        />
      </SectionCard>

      <Accordion variant="contained">
        <Accordion.Item value="raw-settings">
          <Accordion.Control>Advanced: Edit raw settings.toml</Accordion.Control>
          <Accordion.Panel>
            <Stack gap="sm">
              <Text c="dimmed" size="sm">
                Use this editor for parameters not covered above. Changes are validated locally before sending to the API.
              </Text>
              <Textarea
                value={rawContent}
                onChange={(event) => setRawContent(event.currentTarget.value)}
                autosize
                minRows={10}
                styles={{ input: { fontFamily: 'monospace' } }}
              />
              <Stack gap="xs" align="flex-start">
                <Tooltip label="Revert to last saved version">
                  <ActionIcon
                    variant="default"
                    onClick={() => rawQuery.refetch()}
                    disabled={rawQuery.isFetching}
                    aria-label="Reload settings"
                  >
                    <IconRefresh size={18} />
                  </ActionIcon>
                </Tooltip>
                <Button loading={replaceMutation.isPending} onClick={handleRawSave}>
                  Apply changes
                </Button>
              </Stack>
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  )
}
