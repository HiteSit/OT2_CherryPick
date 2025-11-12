import { useEffect, useMemo, useState } from 'react'
import { Button, FileInput, Group, Loader, Paper, Select, Stack, Text, TextInput, Textarea, Title } from '@mantine/core'
import { IconDeviceFloppy, IconTrash, IconUpload } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import {
  useCsvContentQuery,
  useCsvListQuery,
  useDeleteCsv,
  useUploadCsv,
} from '../api/hooks'

export function CsvManager() {
  const csvListQuery = useCsvListQuery()
  const [activeName, setActiveName] = useState<string>('')
  const csvContentQuery = useCsvContentQuery(activeName)
  const uploadMutation = useUploadCsv()
  const deleteMutation = useDeleteCsv()
  const [editorContent, setEditorContent] = useState('')

  useEffect(() => {
    if (csvContentQuery.data !== undefined) {
      setEditorContent(csvContentQuery.data)
    } else if (!activeName) {
      setEditorContent('')
    }
  }, [csvContentQuery.data, activeName])

  const csvOptions = useMemo(
    () => (csvListQuery.data?.files ?? []).map((name) => ({ value: name, label: name })),
    [csvListQuery.data],
  )

  const handleFileUpload = async (file: File | null) => {
    if (!file) return
    const content = await file.text()
    uploadMutation.mutate(
      { name: file.name, content },
      {
        onSuccess: () => {
          setActiveName(file.name)
          notifications.show({ color: 'teal', title: 'CSV uploaded', message: `${file.name} saved.` })
        },
        onError: (error) =>
          notifications.show({ color: 'red', title: 'Upload failed', message: error instanceof Error ? error.message : 'Error' }),
      },
    )
  }

  const handleSave = () => {
    if (!activeName) {
      notifications.show({ color: 'red', title: 'Filename required', message: 'Enter a CSV name before saving.' })
      return
    }
    uploadMutation.mutate(
      { name: activeName, content: editorContent },
      {
        onSuccess: () => notifications.show({ color: 'teal', title: 'CSV saved', message: `${activeName} updated.` }),
        onError: (error) =>
          notifications.show({ color: 'red', title: 'Save failed', message: error instanceof Error ? error.message : 'Error' }),
      },
    )
  }

  const handleDelete = () => {
    if (!activeName) {
      return
    }
    deleteMutation.mutate(activeName, {
      onSuccess: () => {
        notifications.show({ color: 'teal', title: 'Deleted', message: `${activeName} removed.` })
        setActiveName('')
        setEditorContent('')
      },
      onError: (error) =>
        notifications.show({ color: 'red', title: 'Delete failed', message: error instanceof Error ? error.message : 'Error' }),
    })
  }

  return (
    <Stack gap="lg">
      <Title order={4}>CSV Manager</Title>
      <Paper withBorder radius="md" p="md">
        <Stack gap="md">
          {csvListQuery.isLoading ? (
            <Group gap="xs">
              <Loader size="sm" />
              <Text c="dimmed">Loading available CSV files...</Text>
            </Group>
          ) : (
            <Select
              label="Existing CSV files"
              placeholder="Select a CSV to edit"
              searchable
              data={csvOptions}
              value={activeName}
              onChange={(value) => value && setActiveName(value)}
              nothingFoundMessage="No CSV files in workspace."
            />
          )}
          <FileInput
            label="Upload CSV file"
            placeholder="Drop or select a CSV"
            accept=".csv,text/csv"
            leftSection={<IconUpload size={16} />}
            onChange={handleFileUpload}
          />
        </Stack>
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Stack gap="md">
          <TextInput
            label="Active filename"
            placeholder="example_basic.csv"
            value={activeName}
            onChange={(event) => setActiveName(event.currentTarget.value)}
          />
          {csvContentQuery.isFetching && activeName ? (
            <Group gap="xs">
              <Loader size="sm" />
              <Text c="dimmed">Loading CSV content...</Text>
            </Group>
          ) : (
            <Textarea
              label="CSV content"
              minRows={12}
              autosize
              value={editorContent}
              onChange={(event) => setEditorContent(event.currentTarget.value)}
              styles={{ input: { fontFamily: 'monospace', fontSize: '0.85rem' } }}
              placeholder="Source Labware,Source Well,Volume (ul),..."
            />
          )}
          <Group>
            <Button
              leftSection={<IconDeviceFloppy size={16} />}
              onClick={handleSave}
              loading={uploadMutation.isPending}
            >
              Save CSV
            </Button>
            <Button
              color="red"
              variant="light"
              leftSection={<IconTrash size={16} />}
              disabled={!activeName}
              loading={deleteMutation.isPending}
              onClick={handleDelete}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Paper>
    </Stack>
  )
}
