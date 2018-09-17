"""
Utility functions

"""
from operator import add

def calc_mean_energy(vector):
    avg = []
    n = int(len(vector)/1024)

    for i in range(0, n):
        avg.append(sum(vector[i*1024:i*1024+1024])/1024)

    #print avg
    return sum(avg)/len(avg)


def availability(channels, bandwidth, vector):
    a = [0]*len(channels)
    i = 0
    for ch in channels:
        avg_energy = find_average(vector)
        # Decide if channel is empty
        if (avg_energy < -43):
            print 'EMPTY CHANNEL'
            a[i] = 0
        else:
            a[i] = 1
        i = i+1
    return a


"""
neighborsU: list of neighbors U vectors
"""
def calc_vectorN(neighborsU):
    # Get first u
	tmp = neighborsU[0]
	for i in range(1, len(neighborsU)):
		tmp = list( map(add, tmp, neighborsU[i]) )

	return [x if x < 2 else 2 for x in tmp]


def is_empty(avg):
    if (avg<-43):
        print "EMPTY CHANNEL"
        return 0
    else:
        return 1


def detect_collision(avg, c_freq, threshold, b_freq):
	if (avg<-43):
    	print "EMPTY CHANNEL"
		return 0
	elif (avg>treshold-1) and (avg<threshold+1):
   		print "NO COLLISIONS"
		return 1
    else:
    	print "COLLISION"
    	#busy.transmit_busy(b_freq)
    	return 2


def cost(u_vector, busy_tone_channels, penalty, prize):
	c = [0]*len(u_vector)
	for i in range(0, len(u_vector)):
		if (u_vector[i]==1):
			channel_state = decision.is_empty(busy_tone_channels[i])
			if (channel_state==0):
				c[i] = c[i] + prize
			else:
				c[i] = c[i] + penalty
	return c
