const axios = require('axios')
const { ArgumentParser } = require('argparse')
const fs = require('fs')
const credentials = require('./credentials.json')

const session = axios.create({
    headers: {
        'Accept': 'application/vnd.twitchtv.v5+json',
        'Client-ID': credentials.client_id
    }
})

async function getUserId(channel) {
    await new Promise(r => setTimeout(r, 80))
    const response = await session.get(`https://api.twitch.tv/helix/users?login=${channel}`)
    return response.data.data[0].id
}

async function getVideoData(userId, videoCount, videoId) {
    let response
    await new Promise(r => setTimeout(r, 80))
    if (userId) {
        response = await session.get(`https://api.twitch.tv/helix/videos?user_id=${userId}&type=archive&first=${videoCount}`)
    }
    else {
        response = await session.get(`https://api.twitch.tv/helix/videos?id=${videoId}`)
    }
    const videoData = { videoIds: [], channel: response.data.data[0].user_name }
    for (const video of response.data.data) {
        videoData.videoIds.unshift(video.id)
    }
    return videoData
}

async function downloadChat(videoData) {
    const queue = []
    const finished = []
    let fileName = videoData.channel + ' '
    for (const videoId of videoData.videoIds) {
        queue.push(videoId)
    }
    if (queue[0] === queue.at(-1)) {
        fileName += queue[0] + '.txt'
    }
    else {
        fileName += `${queue[0]} to ${queue.at(-1)}.txt`
    }
    console.clear()
    console.log(`Queue:            ${queue}\nFinished:         ${finished}`)
    if (!fs.existsSync('./chats')) {
        fs.mkdirSync('./chats')
    }
    const stream = fs.createWriteStream(`./chats/${fileName}`)
    for (const videoId of videoData.videoIds) {
        let cursor = 'content_offset_seconds=0'
        while (cursor) {
            await new Promise(r => setTimeout(r, 80))
            const response = await session.get(`https://api.twitch.tv/v5/videos/${videoId}/comments?${cursor}`)
            for (const comment of response.data.comments) {
                const offset = Math.floor(comment.content_offset_seconds)
                const hours = Math.floor(offset / 3600).toString().padStart(2, '0')
                const minutes = (Math.floor(offset / 60) % 60).toString().padStart(2, '0')
                const seconds = (offset % 60).toString().padStart(2, '0')
                const timeString = `${hours}h${minutes}m${seconds}s`
                stream.write(`[https://www.twitch.tv/videos/${videoId}?t=${timeString}] ${comment.commenter.display_name}: ${comment.message.body}\n`)
            }
            if ('_next' in response.data) {
                cursor = `cursor=${response.data._next}`
            }
            else {
                cursor = null
                stream.write('\n\n')
            }
        }
        finished.push(queue.shift())
        console.clear()
        console.log(`Queue:            ${queue}\nFinished:         ${finished}`)
    }
}

;(async function () {
    await new Promise(r => setTimeout(r, 80))
    const response = await session.post(`https://id.twitch.tv/oauth2/token?client_id=${credentials.client_id}&client_secret=${credentials.client_secret}&grant_type=client_credentials`)
    session.defaults.headers['Authorization'] = `Bearer ${response.data.access_token}`

    const parser = new ArgumentParser()
    parser.add_argument('-v', '--video_id', { type: 'int', help: 'Chatlogs of video to download. Parameter to be used on its own.' })
    parser.add_argument('-c', '--channel', { help: 'Twitch channel to download chatlogs from. If number of past VODs is not specified it defaults to the latest VOD only.' })
    parser.add_argument('-n', '--number', { type: 'int', help: 'Number of past VODs to download chatlogs from (max 100). Parameter to be used in combination with -c' })
    const args = parser.parse_args()

    if (args.video_id) {
        const videoData = await getVideoData(null, null, args.video_id)
        await downloadChat(videoData)
    }
    else if (args.channel && args.number) {
        const userId = await getUserId(args.channel)
        const videoData = await getVideoData(userId, args.number, null)
        await downloadChat(videoData)
    }
    else if (args.channel) {
        const userId = await getUserId(args.channel)
        const videoData = await getVideoData(userId, 1, null)
        await downloadChat(videoData)
    }
    else if (args.number) {
        console.log('No channel specified.')
    }
    else {
        console.log('No parameters specified.')
    }
})()