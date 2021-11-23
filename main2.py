#------------------------------------------
#Bot que hace quiz, basado en:
#towardsdatascience.com/ creating-a-telegram-chatbot-quiz-with-python-711a43c0c424
#towardsdatascience.com/ bring-your-telegram-chatbot-to-the-next-level-c771ec7d31e4
#A partir de los ejemplos en repositorio dado.
#------------------------------------------
#Importe de datos
import os
import logging
from telegram.ext import PollHandler, Updater, CommandHandler, Filters, MessageHandler
from telegram import Poll
import requests
import random
import re

#Preguntas:

#De multiples respuestas:
pregunta_variada = [
     ["¿Cuáles de los siguientes son realmente Git Hooks?", ['pre-commit', 'post-origin', 'commit-msg'], [0, 2]],
     ["¿Qué comando se relaciona directamente con las ramas del repositorio?", ['git checkout', 'git add', 'git branch'], [0, 2]],
     ["¿Cuáles son opciones para git reset?", ['extreme', 'hard', 'soft'], [1, 2]],
     ["¿Qué languages se pueden ocupar para generar Git Hooks?", ['python', 'B++', 'shell'], [0, 2]]
]

preguntas = [
#Respuesta unica
     ["¿A qué comando se parece a 'git blame'?", ['git log', 'git pull', 'git branch'], 0],
     ["¿Qué tipo de repositorio es el que nace por un fork?", ['nonbare', 'bare', 'ninguno'], 1],
     ["¿Qué representa un 'blob'?", ['objeto', 'directorio', 'nombre'], 0],
     ["¿Para qué sirve 'git bisect'?", ['identificar el autor de un commit', 'identificar un commit  con error', 'eliminar un directorio'], 1],
     ["¿Por qué se utilizaria 'cherry-pick' en vez de un merge?", ['para agregar mas de un commit a HEAD', 'para crear una rama', 'para agregar los cambios de un commit especifico de una rama'], 2],
     ["¿Cuál es la diferencia entre 'git fetch' y 'git pull'?", ['fetch copia los datos remotos nuevos pero no los integra', 'pull sube datos al repositorio remoto', 'fetch borra datos antiguos'], 0],
     ["¿Con qué comando puedes anadir archivos a tu area de staging?", ['git init project', 'git create', 'git add <nombre_archivo>'], 2],
     ["¿Qué es 'origin' en Git?", ['el primer commit del proyecto', 'una forma de nombrar a la rama principal', 'un nombre para el repositorio del cual se origino el proyecto'], 2]
]

#De las que saldran con respuesta
efectivas_poll = []
total_quiz_preguntas = 4
total_pregunta_variada = 2
grade = 1
#Listas que randomizaran la eliminacion de preguntas.
tq_preguntas = []
tp_preguntas = []
hay_poll = False

#Distinguir el identificador para encontrar una sesion de chat especifica que es la que se hace con el bot.
def sacar_chat_id(update, context):
    chat_id = -1
    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id
    elif update.poll is not None:
        chat_id = context.bot_data[update.poll.id]

    return chat_id
#Informacion
def ayuda_comando(update, context):
    msg = """/start da inicio al test.
    /help muestra la ayuda"""
    context.bot.send_message(
        chat_id = sacar_chat_id(update, context),
        text = msg
    )

def poll_aplicador(update, context):
    """
    question = update.poll.question
    correct_answer = update.poll.correct_option_id
    options = update.poll.options
    option_1_vote = update.poll.options[0].voter_count
    """
#Llamar:
    global grade
    q_type = update.poll.type
    context.bot.send_message(
        chat_id = sacar_chat_id(update, context),
        text = 'Comprobando...'
    )

    ans = sacar_respuestas(update)

    if q_type == 'Quiz':
        is_correct = caso_correctas(ans, update)
    else:
        is_correct = correcion_preguntas(ans, update)
    if is_correct:
        msg = 'Excelente'
        grade += 1
    else:
        msg = 'Seguimos...'

    context.bot.send_message(
        chat_id = sacar_chat_id(update, context),
        text = msg
    )

    siguiente_poll(update, context)

#Revision
def correcion_preguntas(ans, update):
    respuestas = update.poll.options

    for id in efectivas_poll:
        if ans == respuestas[id].text:
            return True
    
    return False

def caso_correctas(ans, update):
    respuestas = update.poll.options

    if ans == respuestas[update.poll.correct_option_id].text:
        return True

    return False

#Del contador y update
def sacar_respuestas(update):
    respuestas = update.poll.options

    ret = ""

    for answer in respuestas:
        if answer.voter_count == 1:
            ret = answer.text
            break
    
    return ret
#Llamar variables
def ejecucion_comandos(update, context):
    global tp_preguntas
    global tq_preguntas

    if not hay_poll:
        tq_preguntas = random.sample(preguntas, 4)
        tp_preguntas = random.sample(pregunta_variada, 2)

        siguiente_poll(update, context)
    else:
        context.bot.send_message(
            chat_id = sacar_chat_id(update, context),
            text = 'Ya hay un test en desarollo'
        )
def siguiente_poll(update, context):
    global total_quiz_preguntas
    global total_pregunta_variada
    global grade
    global hay_poll

    if total_quiz_preguntas > 0:
        agregar_pregunta(update, context)
        total_quiz_preguntas -= 1
    elif total_pregunta_variada > 0:
        agregar_pregunta_poll(update, context)
        total_pregunta_variada -= 1
    else:
        #Preguntar de nuevo
        total_pregunta_variada = 2
        total_quiz_preguntas = 4

        context.bot.send_message(
            chat_id = sacar_chat_id(update, context),
            text = 'Has terminado, tu score es ' + str(grade)
        )

        grade = 1
        hay_poll = False
        return False

    hay_poll = True
    return True

def agregar_pregunta(update, context):
    global tq_preguntas
    c_id = sacar_chat_id(update, context)

    _preguntas = random.choice(tq_preguntas)
    tq_preguntas.remove(_preguntas)

    q = _preguntas[0]
    a = _preguntas[1]
    ca = _preguntas[2]

    msg = context.bot.send_poll(chat_id = c_id, question = q, options=a, type = Poll.QUIZ, correct_option_id=ca)
    context.bot_data.update({msg.poll.id: msg.chat.id})

def agregar_pregunta_poll(update, context):
    global efectivas_poll
    global tp_preguntas

    c_id = sacar_chat_id(update, context)

    _preguntas = random.choice(tp_preguntas)
    tp_preguntas.remove(_preguntas)

    q = _preguntas[0]
    a = _preguntas[1]
    efectivas_poll = _preguntas[2]

    msg = context.bot.send_poll(chat_id = c_id, question = q, options=a, type = Poll.REGULAR)
    context.bot_data.update({msg.poll.id: msg.chat.id})

def ejecutor_principal(update, context):
    pass
#Codigo principal
def main():
#Uso del codigo para el bot:
    updater = Updater('2111222219:AAH9FhbjdQAYdcOt4bTy60K3HdJVNFMBRk4', use_context=True)
    dp = updater.dispatcher
    #Comandos
    dp.add_handler(CommandHandler("help", ayuda_comando))
    dp.add_handler(CommandHandler("start", ejecucion_comandos))
    #Mensaje
    dp.add_handler(MessageHandler(Filters.text, ejecutor_principal))
    #Quiz / Preguntas
    dp.add_handler(PollHandler(poll_aplicador, pass_chat_data=True, pass_user_data=True))
    #Empezar
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()