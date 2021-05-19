prepare:
	cp ffmpeg ./functions/split/ffmpeg
	cp ffmpeg ./functions/transcode/ffmpeg
	cp ffmpeg ./functions/snapshot/ffmpeg
	cp ffprobe ./functions/snapshot/ffprobe

deploy: prepare
	fun deploy -y