import React, { useState } from 'react'
import {useQuery} from 'react-query'
import {useLocation} from 'react-router-dom'
import axios from "axios"
import {Prueba} from "../interfaces"
import {
    Alert, AlertDescription,
    AlertIcon,
    AlertTitle,
    Box,
    Button,
    Card, CloseButton,
    Heading,
    Spinner,
    Stack,
    Text,
    Image,
    Center,
    Checkbox,
    useDisclosure,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalCloseButton,
    ModalHeader,
    ModalBody,
    ModalFooter,
} from "@chakra-ui/react"
import {Preguntas} from "../components/Preguntas";
import Agenda from "../components/Agenda";
import MarkdownRenderer from "../components/MarkdownRenderer";

const fetchPrueba = async (codigo: string): Promise<Prueba> => {
    try {
        const resp = await axios.get(`/api/tests/tests/?codigo=${codigo}`)
        return resp.data
    } catch (error: any) {
        const errorMsg = error.response.data[0] || error.response.data.detail || "Algo salió mal"
        throw new Error(errorMsg)
    }
}

function useQueryParams() {
    return new URLSearchParams(useLocation().search)
}

const TestPage: React.FC = () => {
    const queryParams = useQueryParams()
    const codigo = queryParams.get('codigo') || ''
    const [introAceptada, setIntroAceptada] = useState<boolean>(false)
    const [preguntasRespondidas, setPreguntasRespondidas] = useState<boolean>(false)
    const [entrevistaAgendada, setEntrevistaAgendada] = useState<boolean>(false)
    const [terminado, setTerminado] = useState<boolean>(false)
    const [terminosAceptados, setTerminosAceptados] = useState<boolean>(false)
    const { isOpen, onOpen, onClose } = useDisclosure()

    const terminar = () => {
        window.close()
        setTerminado(true)
    }

    const {data: prueba, isLoading, error} = useQuery<Prueba, Error>(
        ['fetchPrueba', codigo],
        () => fetchPrueba(codigo),
        {refetchOnWindowFocus: false}
        )

    const itemsAlignment = preguntasRespondidas ? "start" : "center"
    const mostrarLogo = isLoading || error || !introAceptada || terminado || entrevistaAgendada

    return (
        <Box
            display="flex"
            justifyContent="center"
            alignItems={itemsAlignment}
            p="20px"
            mt="20px"
            alignContent={itemsAlignment}
        >
            <Box width="100%" maxW="500px">
                {mostrarLogo && (
                    <Box display="flex" justifyContent="center">
                        <Image src='/static/images/psicologico_ISOLOGO.svg' alt='logo_el_psicologico' mb="80px" width="xs" />
                    </Box>
                )}
                {isLoading ? (
                    <Center>
                        <Spinner speed="1s" size="xl" />
                    </Center>
                ) : error ? (
                    <Alert status="error">
                        <AlertIcon />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>{error.message}</AlertDescription>
                    </Alert>
                ) : terminado ? (
                    <Card p="10px">
                        <Text>Ya puedes cerrar tu navegador manualmente, nosotros lo intentamos pero no se pudo.</Text>
                    </Card>
                ) : entrevistaAgendada ? (
                        <Card p="10px">
                            <Alert status="success">
                                <AlertDescription>La entrevista ha sido agendada con éxito.</AlertDescription>
                                <CloseButton position="absolute" right="8px" top="8px" onClick={terminar}/>
                            </Alert>
                        </Card>
                ) : preguntasRespondidas ? (
                    <Card p="10px">
                        <Agenda codigo={codigo} successCallback={() => setEntrevistaAgendada(true)} />
                    </Card>
                ) : introAceptada ? (
                    <Preguntas preguntas={prueba!.preguntalikertnoas_set} codigo={codigo} successCallback={() => setPreguntasRespondidas(true)} />
                ) : (
                    <Card p="10px">
                        <Stack spacing="15px">
                            <Box mb="30px">
                                <Heading size="lg" textAlign="center">Test de control de los impulsos</Heading>
                            </Box>
                            <Text>Hola!</Text>
                            <Text>Bienvenido(a) a esta evaluación online.</Text>
                            <Text>A continuación leerás una serie de oraciones con alternativas de respuesta.</Text>
                            <Text>En cada caso selecciona aquella que más te represente, sin pensarlo demasiado.</Text>
                            <Box display="flex" justifyContent="center" mt={5} mb={2}>
                                <Button
                                    colorScheme="teal"
                                    isDisabled={!terminosAceptados}
                                    onClick={() => setIntroAceptada(true)}
                                >
                                    Comenzar test
                                </Button>
                            </Box>
                            <Box alignSelf="end">
                                <Checkbox
                                    checked={terminosAceptados}
                                    onChange={(e) => {
                                        setTerminosAceptados(e.target.checked)
                                    }}
                                >
                                    Acepto los <Button variant="link" onClick={onOpen}>Términos y Condiciones</Button>
                                </Checkbox>
                            </Box>
                        </Stack>
                    </Card>
                )}
            </Box>
            <Modal isOpen={isOpen} onClose={onClose}>
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>Términos y Condiciones</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody>
                        <MarkdownRenderer url="/static/terminos_y_condiciones/control_de_impulsos.md"/>
                    </ModalBody>
                    <ModalFooter>
                        <Button onClick={onClose}>Cerrar</Button>
                    </ModalFooter>
                </ModalContent>
            </Modal>
        </Box>
    )
}

export default TestPage
