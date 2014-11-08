import os, datetime, pyshark, sys
from cStringIO import StringIO

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'static/tracefiles/')


def get_capture_count(traceFile):
	# p = pcap.pcapObject()
	# p.open_offline(str(os.path.join(UPLOAD_FOLDER, traceFile.filename)))

	# count = []
	
	# def counter(*args):
	# 	count.append(args[0])

	# p.dispatch(0, counter)

	# return len(count)
	# 
	return 5

def decode_capture_file_summary(traceFile):
	cap = pyshark.FileCapture(os.path.join(UPLOAD_FOLDER, traceFile.filename), only_summaries=True, keep_packets=False)


	details = {
		'stats': {
			'breakdown': {},
			'length_buckets': {'0-200': 0, '201-450': 0, '451-800':0, '801-1200':0, '1201-1500': 0},
			'count': 0
		},
		'packets': [],
		# 'linechart': []
		}
	avg_length = []
	
	

	def decode_packet(packet):

		pkt_details = {
			'number' : packet.no,
			'length' : packet.length,
			'time' : packet.time,
			'delta' : packet.delta,
		}
		pkt_details['src_ip'] = packet.source
		pkt_details['dst_ip'] = packet.destination
		pkt_details['protocol'] = packet.protocol

		pkt_details['desc'] = packet.info

		details['packets'].append(pkt_details)
		avg_length.append(int(packet.length))

		if 0 <= int(packet.length) <= 200:
			details['stats']['length_buckets']['0-200'] += 1
		elif 201 <= int(packet.length) <= 450:
			details['stats']['length_buckets']['201-450'] += 1
		elif 451 <= int(packet.length) <= 800:
			details['stats']['length_buckets']['451-800'] += 1
		elif 801 <= int(packet.length) <= 1200:
			details['stats']['length_buckets']['801-1200'] += 1
		elif 1201 <= int(packet.length):
			details['stats']['length_buckets']['1201-1500'] += 1

		try:
			details['stats']['breakdown'][packet.protocol] += 1
		except KeyError:
			details['stats']['breakdown'][packet.protocol] = 1


	try:
		cap.apply_on_packets(decode_packet, timeout=30)
	except:
		return 'Capture File is too large, please try downloading and analyzing locally.'

	details['stats']['avg_length'] = sum(avg_length) / len(avg_length)
	details['stats']['count'] = len(avg_length)

	return details


def get_packet_detail(traceFile, number):
	cap = pyshark.FileCapture(os.path.join(UPLOAD_FOLDER, traceFile.filename))

	old_stdout = sys.stdout
	sys.stdout = mystdout = StringIO()

	cap[number-1].pretty_print()

	sys.stdout = old_stdout

	detail = ''

	for line in mystdout.getvalue().split('\n'):
		if line == 'self._packet_string':
			continue
		elif 'Layer ETH' in line:
			detail += '''<div class="panel panel-default">
						  <div class="panel-heading" role="tab" id="headingOne">
						    <h4 class="panel-title">
						      <a data-toggle="collapse" href="#%(link)s" aria-expanded="true" aria-controls="%(name)s">
						        %(name)s
						      </a>
						    </h4>
						  </div>
						  <div id="%(link)s" class="panel-collapse collapse in" role="tabpanel" aria-labelledby="headingOne">
						    <div class="panel-body">

			''' % {'name': line[:-1], 'link': line.replace(' ', '-').strip(':')}
		elif 'Layer' in line:
			detail += '''</div>
						  </div>
						</div>
						<div class="panel panel-default">
						  <div class="panel-heading" role="tab" id="headingOne">
						    <h4 class="panel-title">
						      <a class="collapsed" data-toggle="collapse" href="#%(link)s" aria-expanded="true" aria-controls="%(name)s">
						        %(name)s
						      </a>
						    </h4>
						  </div>
						  <div id="%(link)s" class="panel-collapse collapse" role="tabpanel" aria-labelledby="headingOne">
						    <div class="panel-body">

			''' % {'name': line[:-1], 'link': line.replace(' ', '-').strip(':')}
		else:	
			detail += '<p>%s</p>\n' % line

	detail += '</div></div></div>'
	return detail


def decode_capture_file_detailed(traceFile):
	cap = pyshark.FileCapture(os.path.join(UPLOAD_FOLDER, traceFile.filename)) # , display_filter='ip'


	details = {
		'stats': {
			'breakdown': {},
			'length_buckets': {'0-200': 0, '201-450': 0, '451-800':0, '801-1200':0, '1201-1500': 0},
			'count': 0
		},
		'packets': [],
		# 'linechart': []
		}
	avg_length = []
	
	

	def decode_packet(packet):

		pkt_details = {
			'number' : packet.frame_info.number,
			'length' : packet.length,
			'timestamp' : packet.sniff_time.isoformat()[:-4]
		}
		try:
			pkt_details['ttl'] = packet.ip.ttl
			pkt_details['src_ip'] = packet.ip.src
			pkt_details['dst_ip'] = packet.ip.dst
		except:
			try:
				pkt_details['ttl'] = packet.ipv6.hlim
				pkt_details['src_ip'] = packet.ipv6.src
				pkt_details['dst_ip'] = packet.ipv6.dst
			except:
				pass


		try:
			pkt_details['dst_port'] = packet[packet.transport_layer].dstport
			pkt_details['src_port'] = packet[packet.transport_layer].srcport
			pkt_details['protocol'] = packet.highest_layer
		except:
			pass

		try:
			pkt_details['desc'] = packet[packet.highest_layer].chat
		except:
			try:
				if packet.dns.flags_response:
					pkt_details['desc'] = 'DNS Response: %s' % (packet.dns.qry_name)
				elif packet.dns.flags_response == 0:
					pkt_details['desc'] = 'DNS Request: %s' % (packet.dns.qry_name)
			except:
				pass

		details['packets'].append(pkt_details)
		avg_length.append(int(packet.length))

		if 0 <= int(packet.length) <= 200:
			details['stats']['length_buckets']['0-200'] += 1
		elif 201 <= int(packet.length) <= 450:
			details['stats']['length_buckets']['201-450'] += 1
		elif 451 <= int(packet.length) <= 800:
			details['stats']['length_buckets']['451-800'] += 1
		elif 801 <= int(packet.length) <= 1200:
			details['stats']['length_buckets']['801-1200'] += 1
		elif 1201 <= int(packet.length):
			details['stats']['length_buckets']['1201-1500'] += 1

		try:
			details['stats']['breakdown'][packet.highest_layer] += 1
		except KeyError:
			details['stats']['breakdown'][packet.highest_layer] = 1


	cap.apply_on_packets(decode_packet, timeout=200)

	details['stats']['avg_length'] = sum(avg_length) / len(avg_length)
	details['stats']['count'] = len(avg_length)

	return details

